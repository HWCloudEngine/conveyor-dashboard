#    Copyright 2013, Big Switch Networks, Inc.
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

from openstack_dashboard.dashboards.project.loadbalancers.\
    tables import PoolsTable

from conveyordashboard.common import constants as consts
from conveyordashboard.overview import tables as overview_tables


class PoolsTable(PoolsTable):

    class Meta(object):
        name = "poolstable"
        verbose_name = _("Pools")
        css_classes = ' '.join(['table-res', consts.NEUTRON_POOL])
        table_actions = (overview_tables.CreatePlanWithMulRes,
                         overview_tables.CreateMigratePlanWithMulRes)
        row_actions = (overview_tables.CreateClonePlan,
                       overview_tables.CreateMigratePlan,)
