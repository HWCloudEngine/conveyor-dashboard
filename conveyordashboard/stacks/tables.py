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

from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import tables
from horizon.utils import filters

from conveyordashboard.common import actions as common_actions
from conveyordashboard.common import constants as consts
from conveyordashboard.common import resource_state


class CreatePlan(common_actions.CreatePlan):
    def allowed(self, request, stack=None):
        return stack.stack_status in resource_state.STACK_CLONE_STATE


class StacksFilterAction(tables.FilterAction):

    def filter(self, table, stacks, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [stack for stack in stacks
                if query in stack.name.lower()]


class StacksTable(tables.DataTable):
    STATUS_CHOICES = (
        ("Complete", True),
        ("Failed", False),
    )
    STACK_STATUS_DISPLAY_CHOICES = (
        ("create_complete", pgettext_lazy("current status of stack",
                                          u"Create Complete")),
    )
    name = tables.Column("stack_name",
                         verbose_name=_("Stack Name"),
                         link="horizon:project:stacks:detail",)
    created = tables.Column("creation_time",
                            verbose_name=_("Created"),
                            filters=(filters.parse_isotime,
                                     filters.timesince_or_never))
    updated = tables.Column("updated_time",
                            verbose_name=_("Updated"),
                            filters=(filters.parse_isotime,
                                     filters.timesince_or_never))
    status = tables.Column("status",
                           hidden=True,
                           status_choices=STATUS_CHOICES)

    stack_status = tables.Column("stack_status",
                                 verbose_name=_("Status"),
                                 display_choices=STACK_STATUS_DISPLAY_CHOICES)

    def get_object_display(self, stack):
        return stack.stack_name

    class Meta(object):
        name = "stacks"
        verbose_name = _("Stacks")
        css_classes = "table-res %s" % consts.HEAT_STACK
        pagination_param = 'stack_marker'
        status_columns = ["status", ]
        table_actions = (common_actions.CreatePlanWithMultiRes,)
        row_actions = (CreatePlan,)
