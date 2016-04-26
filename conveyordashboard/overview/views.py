# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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
from django.utils.translation import ugettext_lazy as _
from django.utils.datastructures import SortedDict
from django.views import generic

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import memoized

from openstack_dashboard import api as os_api

from conveyordashboard.api import api
from conveyordashboard.instances import topology
from conveyordashboard.overview import forms as overview_forms
from conveyordashboard.overview import tables as overview_tables

from conveyordashboard.instances.tables import InstancesTable
from conveyordashboard.volumes.volumes.tables import VolumesTable

LOG = logging.getLogger(__name__)


class IndexView(tables.MultiTableView):
    table_classes = (overview_tables.InstancesTable,
                     overview_tables.VolumesTable,
                     overview_tables.NetworksTable,
                     overview_tables.SubnetsTable,
                     overview_tables.RoutersTable,)
    page_title = _("Overview")
    template_name = "overview/index.html"

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        actions_table = overview_tables.ActionsTable(self.request)
        context["actions"] = actions_table.render_table_actions()
        return context

    def get_instances_data(self):
        try:
            instances, self._more = api.server_list(self.request)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve instances list.'))
        if instances:
            try:
                images = api.resource_list(self.request, "OS::Glance::Image")
            except Exception:
                images = []
                exceptions.handle(self.request, ignore=True)

            image_map = SortedDict([(str(image.id), image)
                                    for image in images])

            # Loop through instances to get flavor info.
            for instance in instances:
                if hasattr(instance, 'image'):
                    # Instance from image returns dict
                    if isinstance(instance.image, dict):
                        if instance.image.get('id') in image_map:
                            instance.image = image_map[instance.image['id']]
        return instances

    def get_volumes_data(self):
        try:
            volumes = api.resource_list(self.request, "OS::Cinder::Volume")
            volumes = [os_api.cinder.Volume(v) for v in volumes]
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve volumes list.'))
        return volumes

    def get_networks_data(self):
        try:
            nets = api.net_list_for_tenant(self.request,
                                           self.request.user.tenant_id)
        except Exception: 
            exceptions.handle(self.request,
                              _("Unable to retrieve network list."))
        return nets

    def get_subnets_data(self):
        try:
            return api.subnet_list_for_tenant(self.request,
                                              self.request.user.tenant_id)
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve subnets list."))

    def get_routers_data(self):
        try:
            routers = api.resource_list(self.request, "OS::Neutron::Router")
            return [os_api.neutron.Router(r.__dict__) for r in routers]
        except Exception:
            exceptions.handle((self.request,
                               _("Unable to retrieve routers list.")))


class PlanTopologyView(forms.ModalFormView):
    form_class = overview_forms.PlanForm
    form_id = "plan_topology_form"
    modal_header = _("Plan Topology")
    template_name = 'overview/topology.html'
    context_object_name = 'plan'
    submit_url = reverse_lazy("horizon:conveyor:overview:create_plan")
    success_url = reverse_lazy("horizon:conveyor:overview:index")
    page_title = _("Plan Topology")

    def get_context_data(self, **kwargs):
        context = super(PlanTopologyView, self).get_context_data(**kwargs)

        self.set_success_url()

        plan, is_original = self.get_object()

        context['plan'] =  plan
        context['plan_id'] = plan.plan_id

        d3_data = topology.load_plan_d3_data(self.request, plan, is_original)
        context['d3_data'] = d3_data
        context['is_original'] = is_original

        context['azs'] = self.get_zones()

        try:
            context["type"] = self.request.GET["type"]
        except Exception:
            redirect = PlanTopologyView.success_url
            msg = _("Query string does not contain parameter plan type.")
            exceptions.handler(self.request, msg, redirect=redirect)

        return context

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        LOG.info("request={}".format(self.request))
        if "ids" in self.request.GET:
            resource = []
            id_list = {}
            try:
                ids = self.request.GET["ids"]
                plan_type = self.request.GET["type"]
                LOG.info("ids=%s, plan_type=%s" % (ids, plan_type))
                for item in ids.split("**"):
                    id_list[item.split("*")[0]] = item.split("*")[1].split(",")
                for key, value in id_list.items():
                    for id in value:
                        resource.append({"type": key, "id": id})
                return api.plan_create(self.request, plan_type, resource), True
            except Exception as e:
                redirect = PlanTopologyView.success_url
                msg = _("Query string is not a correct format. error=%s"%str(e))
                exceptions.handle(self.request, msg, redirect=redirect)
                return
        elif "plan_id" in self.request.GET:
            try:
                return api.plan_get(self.request, self.request.GET["plan_id"]), False
            except Exception:
                redirect = PlanTopologyView.success_url
                msg = _('Unable to retrieve plan details.')
                exceptions.handle(self.request, msg, redirect=redirect)
                return

        redirect = PlanTopologyView.success_url
        msg = _('Query string does not contain either plan_id or res ids.')
        exceptions.handle(self.request, msg, redirect=redirect)

    def get_zones(self, *args, **kwargs):
        try:
            zones = api.availability_zone_list(self.request)
            return zones
        except Exception:
            zones = []
            exceptions.handle(self.request,
                              _('Unable to retrieve availability zones.'))

    def set_success_url(self):
        try:
            if "next_url" in self.request.GET:
                PlanTopologyView.success_url = self.request.GET["next_url"]
            else:
                PlanTopologyView.success_url = self.request.HTTP_REFERER
        except:
            pass

    def get_initial(self):
        initial = super(PlanTopologyView, self).get_initial()
        return initial


TYPE_CLASS_MAPPING = {"OS::Nova::Server": InstancesTable,
                      "OS::Cinder::Volume": VolumesTable}

class RowActionsView(generic.View):
    @staticmethod
    def get(request, **kwargs):
        res_type = request.GET["res_type"]
        id = request.GET["id"]
        next_url = request.GET.get("next_url", None)
        res = api.ResourceDetail(request, res_type, id).get()
        if res_type in TYPE_CLASS_MAPPING:
            table = TYPE_CLASS_MAPPING[res_type](request, next_url=next_url)
            actions = table.render_row_actions(res)
            return http.HttpResponse(actions, content_type='text/html')


class TableActionsView(generic.View):
    @staticmethod
    def get(request, **kwargs):
        res_type = request.GET["res_type"]
        if res_type in TYPE_CLASS_MAPPING:
            table = TYPE_CLASS_MAPPING[res_type](request)
            table_actions = table.render_table_actions()
            return http.HttpResponse(table_actions, content_type='text/html')
