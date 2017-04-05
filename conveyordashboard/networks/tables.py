# Copyright (c) 2017 Huawei, Inc.
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

from django.utils.translation import ugettext_lazy as _

from horizon import tables

from openstack_dashboard.dashboards.project.networks.subnets.tables \
    import SubnetsTable
from openstack_dashboard.dashboards.project.networks.tables \
    import NetworksTable
from openstack_dashboard.dashboards.project.routers.tables import RoutersTable

from conveyordashboard.common import actions as common_actions
from conveyordashboard.common import constants as consts


class NetworksFilterAction(tables.FilterAction):
    def filter(self, table, networks, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [network for network in networks
                if query in network.name.lower()]


class NetworksTable(NetworksTable):
    class Meta(object):
        name = 'networks'
        verbose_name = _("Networks")
        css_classes = "table-res %s" % consts.NEUTRON_NET
        table_actions = (common_actions.CreateClonePlanWithMulRes,
                         common_actions.CreateMigratePlanWithMulRes,
                         NetworksFilterAction)
        row_actions = (common_actions.CreateClonePlan,
                       common_actions.CreateMigratePlan,)


class SubnetsTable(SubnetsTable):
    class Meta(object):
        name = 'subnets'
        hidden_title = False
        verbose_name = _("Subnets")
        css_classes = "table-res %s" % consts.NEUTRON_SUBNET
        table_actions = (NetworksFilterAction,)
        row_actions = (common_actions.CreateClonePlan,
                       common_actions.CreateMigratePlan,)


class RoutersTable(RoutersTable):
    def __init__(self, request, data=None, needs_form_wrapper=None, **kwargs):
        super(RoutersTable, self).__init__(
            request,
            data=data,
            needs_form_wrapper=needs_form_wrapper,
            **kwargs)
        del self.columns['ext_net']

    class Meta(object):
        name = 'routers'
        hidden_title = False
        varbose_name = _("Routers")
        css_classes = "table-res %s" % consts.NEUTRON_ROUTER
        table_actions = (NetworksFilterAction,)
        row_actions = (common_actions.CreateClonePlan,
                       common_actions.CreateMigratePlan,)
