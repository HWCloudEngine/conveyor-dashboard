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

import logging

from django import http
from django.utils.translation import ugettext_lazy as _
from django.utils.datastructures import SortedDict
from django.views import generic

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api as os_api

from conveyordashboard.api import api
from conveyordashboard.overview import tables as overview_tables

from conveyordashboard.instances.tables import InstancesTable
from conveyordashboard.volumes.tables import VolumesTable

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
