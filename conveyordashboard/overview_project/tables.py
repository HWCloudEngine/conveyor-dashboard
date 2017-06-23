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

from conveyordashboard.common import actions as common_actions


class ResTable(tables.DataTable):
    project_id = tables.Column('project_id',
                               verbose_name=_("Project ID"),
                               hidden=True)
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         sortable=False)
    res_type = tables.Column("res_type",
                             verbose_name=_("Resource Type"),
                             sortable=False)
    availability_zone = tables.Column("availability_zone",
                                      verbose_name=_("Availability Zone"),
                                      sortable=False)

    class Meta(object):
        name = 'resource'
        verbose_name = _("Resource")
        table_actions = (common_actions.CreateClonePlanWithMulRes,
                         common_actions.CreateMigratePlanWithMulRes)
        row_actions = (common_actions.CreateClonePlan,
                       common_actions.CreateMigratePlan)
