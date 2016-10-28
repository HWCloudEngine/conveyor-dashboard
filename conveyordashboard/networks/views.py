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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api as os_api

from conveyordashboard.api import api
from conveyordashboard.networks import tables as network_tables
from conveyordashboard.overview import tables as overview_tables


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = network_tables.NetworksTable
    template_name = 'networks/index.html'
    page_title = _("Networks")

    def get_data(self):
        try:
            return api.net_list_for_tenant(self.request,
                                           self.request.user.tenant_id)
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve network list."))

    def get_filters(self, filters):
        filter_action = self.table._meta._filter_action
        if filter_action:
            filter_field = self.table.get_filter_field()
            if filter_action.is_api_filter(filter_field):
                filter_string = self.table.get_filter_string()
                if filter_field and filter_string:
                    filters[filter_field] = filter_string
        return filters

# class IndexView(tables.MultiTableView):
#     table_classes = [network_tables.NetworksTable]
#                      # network_tables.SubnetsTable,
#                      # network_tables.RoutersTable]
#     template_name = 'networks/index.html'
#     page_title = _("Network Group")
#
#     def get_context_data(self, **kwargs):
#         context = super(IndexView, self).get_context_data(**kwargs)
#         actions_table = overview_tables.ActionsTable(self.request)
#         context["actions"] = actions_table.render_table_actions()
#         return context
#
#     def get_networks_data(self):
#         try:
#             return api.net_list_for_tenant(self.request,
#                                            self.request.user.tenant_id)
#         except Exception:
#             exceptions.handle(self.request,
#                               _("Unable to retrieve network list."))
#
#     def get_subnets_data(self):
#         try:
#             return api.subnet_list_for_tenant(self.request,
#                                               self.request.user.tenant_id)
#         except Exception:
#             exceptions.handle(self.request,
#                               _("Unable to retrieve subnets list."))
#
#     def get_routers_data(self):
#         try:
#             routers = api.resource_list(self.request, "OS::Neutron::Router")
#             return [os_api.neutron.Router(r.__dict__) for r in routers]
#         except Exception:
#             exceptions.handle((self.request,
#                                _("Unable to retrieve routers list.")))
