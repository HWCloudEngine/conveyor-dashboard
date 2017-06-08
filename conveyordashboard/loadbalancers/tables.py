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

from openstack_dashboard.dashboards.project.loadbalancers \
    import tables as lb_tables

from conveyordashboard.common import actions as common_actions
from conveyordashboard.common import constants as consts
from conveyordashboard.common import resource_state


class ClonePool(common_actions.CreateClonePlan):
    def allowed(self, request, pool=None):
        if not pool:
            return False
        if pool.status not in resource_state.POOL_CLONE_STATE:
            return False
        return True


class MigratePool(common_actions.CreateMigratePlan):
    def allowed(self, request, pool=None):
        if not pool:
            return False
        if pool.status not in resource_state.POOL_MIGRATE_STATE:
            return False
        return True


class PoolsTable(lb_tables.PoolsTable):

    class Meta(object):
        name = "poolstable"
        verbose_name = _("Pools")
        css_classes = ' '.join(['table-res', consts.NEUTRON_POOL])
        table_actions = (common_actions.CreateClonePlanWithMulRes,
                         common_actions.CreateMigratePlanWithMulRes)
        row_actions = (ClonePool,
                       MigratePool,)
