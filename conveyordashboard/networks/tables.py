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

from openstack_dashboard.dashboards.project.networks import tables \
    as net_tables

from conveyordashboard.common import actions as common_actions
from conveyordashboard.common import constants as consts
from conveyordashboard.common import resource_state


class CloneNetwork(common_actions.CreateClonePlan):
    def allowed(self, request, net=None):
        if not net:
            return False
        if net.status not in resource_state.NET_CLONE_STATE:
            return False
        return True


class MigrateNetwork(common_actions.CreateMigratePlan):
    def allowed(self, request, net=None):
        if not net:
            return False
        if net.status not in resource_state.NET_MIGRATE_STATE:
            return False
        return True


class NetworksFilterAction(tables.FilterAction):
    def filter(self, table, networks, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [network for network in networks
                if query in network.name.lower()]


class NetworksTable(net_tables.NetworksTable):
    class Meta(object):
        name = 'networks'
        verbose_name = _("Networks")
        css_classes = "table-res %s" % consts.NEUTRON_NET
        table_actions = (common_actions.CreateClonePlanWithMulRes,
                         common_actions.CreateMigratePlanWithMulRes,
                         NetworksFilterAction)
        row_actions = (CloneNetwork,
                       MigrateNetwork,)
