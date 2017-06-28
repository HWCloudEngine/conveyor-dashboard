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

from django.core.urlresolvers import reverse
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from conveyordashboard.common import actions as common_actions


class CreateProjectPlan(tables.LinkAction):
    name = 'create_project_plan'
    verbose_name = _("Create Project Plan")
    url = 'horizon:conveyor:plans:create'
    classes = ("ajax-modal", "disabled", "create-project-plan")
    help_text = _("Create plan for all resources of current project")
    icon = 'plus'

    def get_link_url(self, *args):
        base_url = reverse(self.url)
        params = urlencode({
            'ids': 'project*' + self.table.request.user.tenant_id
        })
        return '?'.join([base_url, params])


class CreatePlan(common_actions.CreatePlan):

    def get_link_url(self, datum):
        base_url = reverse(self.url)

        params = urlencode({
            'ids': ''.join([common_actions.get_res_type(datum, self.table),
                            '*',
                            self.table.get_object_id(datum)])
        })
        return '?'.join([base_url, params])


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
        table_actions = (common_actions.CreatePlanWithMultiRes,
                         CreateProjectPlan)
        row_actions = (CreatePlan,)
