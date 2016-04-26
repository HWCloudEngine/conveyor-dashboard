# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 OpenStack Foundation
# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import json
import logging

from django import http
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from horizon import exceptions
from horizon import forms
from horizon.utils import memoized
from horizon import tables
from horizon import views as horizon_views

from conveyordashboard.instances import tables as clone_tables

from openstack_dashboard import api as os_api
from openstack_dashboard.dashboards.project.instances import views
from openstack_dashboard.dashboards.project.instances.workflows \
    import update_instance

from conveyordashboard.api import api
from conveyordashboard.instances import resources
from conveyordashboard.instances import topology

LOG = logging.getLogger(__name__)


class UpdateView(views.UpdateView):
    workflow_class = update_instance.AdminUpdateInstance
    success_url = reverse_lazy("horizon:conveyor:instances:index")


class IndexView(tables.DataTableView):
    table_class = clone_tables.InstancesTable
    template_name = 'instances/index.html'
    page_title = _("Instances")

    def has_more_data(self, table):
        return self._more

    def get_data(self):
        marker = self.request.GET.get(
            clone_tables.InstancesTable._meta.pagination_param, None)
        search_opts = self.get_filters({'marker': marker, 'paginate': True})
        # Gather our instances
        try:
            instances, self._more = api.server_list(self.request,
                                                    search_opts=search_opts)
            LOG.info("instacnes={}".format(instances))
        except Exception:
            self._more = False
            instances = []
            exceptions.handle(self.request,
                              _('Unable to retrieve instances.'))

        if instances:
            try:
                os_api.network.servers_update_addresses(self.request,
                                                        instances)
            except Exception:
                exceptions.handle(
                    self.request,
                    message=_('Unable to retrieve IP addresses from Neutron.'),
                    ignore=True)

            try:
                flavors = api.resource_list(self.request, "OS::Nova::Flavor")
            except Exception:
                flavors = []
                exceptions.handle(self.request, ignore=True)

            try:
                images = api.resource_list(self.request, "OS::Glance::Image")
            except Exception:
                images = []
                exceptions.handle(self.request, ignore=True)

            full_flavors = SortedDict([(str(flavor.id), flavor)
                                       for flavor in flavors])
            image_map = SortedDict([(str(image.id), image)
                                    for image in images])

            # Loop through instances to get flavor info.
            for instance in instances:
                if hasattr(instance, 'image'):
                    # Instance from image returns dict
                    if isinstance(instance.image, dict):
                        if instance.image.get('id') in image_map:
                            instance.image = image_map[instance.image['id']]

                try:
                    flavor_id = instance.flavor["id"]
                    if flavor_id in full_flavors:
                        instance.full_flavor = full_flavors[flavor_id]
                    else:
                        instance.full_flavor = api.resource_detail(
                                                        self.request,
                                                        "OS::Nova::Flavor",
                                                        flavor_id)
                except Exception:
                    msg = ('Unable to retrieve flavor "%s" for instance "%s".'
                           % (flavor_id, instance.id))
                    LOG.info(msg)
        return instances


    def get_filters(self, filters):
        filter_action = self.table._meta._filter_action
        if filter_action:
            filter_field = self.table.get_filter_field()
            if filter_action.is_api_filter(filter_field):
                filter_string = self.table.get_filter_string()
                if filter_field and filter_string:
                    filters[filter_field] = filter_string
        return filters


class CancelCloneJsonView(generic.View):
    @staticmethod
    def get(request, **kwargs):
        try:
            api.plan_delete(request, request.GET['plan_id'])
            LOG.info("Cancel plan %s and delete it "
                     "successfully." % request.GET['plan_id'])
            msg = {"msg": "success"}
        except Exception as e:
            msg = {"msg": "err"}
        return http.HttpResponse(json.dumps(msg),
                                 content_type='application/json')

class ResourceDetailJsonView(generic.View):
    @staticmethod
    def post(request, **kwargs):
        POST = request.POST
        plan_id = POST['plan_id']
        is_original = POST['is_original']
        if is_original == "True":
            is_original = True
        elif is_original == "False":
            is_original = False
        else:
            exceptions.handle(
                    request,
                    message=_('Request parameter is not correct.'),
                    ignore=True)

        resource_type = POST['resource_type']
        resource_id = POST['resource_id']
        update_data = json.JSONDecoder().decode(POST["update_data"])
        updated_res = json.JSONDecoder().decode(POST["updated_res"])
        data = resources.ResourceDetailFromPlan(request,
                                                plan_id,
                                                resource_type,
                                                resource_id,
                                                update_data,
                                                updated_res,
                                                is_original).render()
        resp = {"msg": "success",
                "data": data,
                "image": api.get_resource_image(resource_type, 'red')}
        return http.HttpResponse(json.dumps(resp),
                                 content_type='application/json')


class JSONView(generic.View):
    @staticmethod
    def post(request, **kwargs):
        POST = request.POST
        plan_id = POST['plan_id']
        plan = api.plan_get(request, plan_id)
        i_updated_resources = json.JSONDecoder()\
                                  .decode(POST['updated_resources'])
        updated_resources = plan.original_resources
        updated_resources.update(i_updated_resources)

        i_dependencies = json.JSONDecoder().decode(POST["dependencies"])
        dependencies = plan.original_dependencies
        dependencies.update(i_dependencies)

        data = json.JSONDecoder().decode(POST["data"])
        planupdate = resources.PlanUpdate(request,
                                          plan_id,
                                          updated_resources,
                                          dependencies)
        planupdate.execute(data)
        (updated_resources,
         dependencies,
         update_resource) = planupdate.execute_return()

        (i_updated_resources,
         i_dependencies) = resources.update_return_resource(
                                        i_updated_resources,
                                        updated_resources,
                                        i_dependencies,
                                        dependencies)

        d3_data = topology.load_d3_data(request, plan_id, dependencies)

        resp_data = {"d3_data": d3_data,
                     "update_resources":update_resource.values(),
                     "updated_resources": i_updated_resources,
                     "dependencies": i_dependencies}
        return http.HttpResponse(json.dumps(resp_data),
                                 content_type='application/json')
