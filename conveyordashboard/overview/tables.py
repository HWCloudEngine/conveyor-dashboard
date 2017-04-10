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
from conveyordashboard.common import constants as consts


class Clone(common_actions.CreateClonePlan):
    def allowed(self, request, datnum=None):
        if not datnum:
            return False
        obj = getattr(datnum, 'obj', None)
        if obj is None:
            return False
        if datnum.res_type == consts.NOVA_SERVER:
            return obj.status in ("SHUTOFF",)
        else:
            return True


class Migrate(common_actions.CreateMigratePlan):
    def allowed(self, request, datnum=None):
        if not datnum:
            return False
        obj = getattr(datnum, 'obj', None)
        if obj is None:
            return False
        if datnum.res_type == consts.NOVA_SERVER:
            return obj.status in ("SHUTOFF",)
        else:
            return True


class ActionsTable(tables.DataTable):
    class Meta(object):
        name = 'actions'
        verbose_name = _("Actions")
        table_actions = (common_actions.CreateClonePlanWithMulRes,
                         common_actions.CreateMigratePlanWithMulRes,)


class ResTable(tables.DataTable):
    project_id = tables.Column('project_id', verbose_name=_("Project ID"),
                               hidden=True)
    name = tables.Column("name", verbose_name=_("Name"))
    res_type = tables.Column("res_type", verbose_name=_("Resource Type"))

    class Meta(object):
        name = 'resource'
        verbose_name = _("Resource")
        table_actions = (common_actions.CreateClonePlanWithMulRes,
                         common_actions.CreateMigratePlanWithMulRes)
        row_actions = (Clone, Migrate)
