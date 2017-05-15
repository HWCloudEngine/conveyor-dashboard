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

from django.http import Http404
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import messages
from horizon import tables
from horizon.utils import filters

from conveyordashboard.api import api
from conveyordashboard.common import actions as common_actions
from conveyordashboard.common import constants as consts


class CloneStack(common_actions.CreateClonePlan):
    """"""


class MigrateStack(common_actions.CreateMigratePlan):
    """"""


class StacksUpdateRow(tables.Row):
    ajax = True

    def can_be_selected(self, datum):
        return datum.stack_status != 'DELETE_COMPLETE'

    def get_data(self, request, stack_id):
        try:
            stack = api.get_wrapped_detail_resource(request,
                                                    consts.HEAT_STACK,
                                                    stack_id)
            if stack.stack_status == 'DELETE_COMPLETE':
                # returning 404 to the ajax call removes the
                # row from the table on the ui
                raise Http404
            return stack
        except Http404:
            raise
        except Exception as e:
            messages.error(request, e)
            raise


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
        ("init_in_progress", pgettext_lazy("current status of stack",
                                           u"Init In Progress")),
        ("init_complete", pgettext_lazy("current status of stack",
                                        u"Init Complete")),
        ("init_failed", pgettext_lazy("current status of stack",
                                      u"Init Failed")),
        ("create_in_progress", pgettext_lazy("current status of stack",
                                             u"Create In Progress")),
        ("create_complete", pgettext_lazy("current status of stack",
                                          u"Create Complete")),
        ("create_failed", pgettext_lazy("current status of stack",
                                        u"Create Failed")),
        ("delete_in_progress", pgettext_lazy("current status of stack",
                                             u"Delete In Progress")),
        ("delete_complete", pgettext_lazy("current status of stack",
                                          u"Delete Complete")),
        ("delete_failed", pgettext_lazy("current status of stack",
                                        u"Delete Failed")),
        ("update_in_progress", pgettext_lazy("current status of stack",
                                             u"Update In Progress")),
        ("update_complete", pgettext_lazy("current status of stack",
                                          u"Update Complete")),
        ("update_failed", pgettext_lazy("current status of stack",
                                        u"Update Failed")),
        ("rollback_in_progress", pgettext_lazy("current status of stack",
                                               u"Rollback In Progress")),
        ("rollback_complete", pgettext_lazy("current status of stack",
                                            u"Rollback Complete")),
        ("rollback_failed", pgettext_lazy("current status of stack",
                                          u"Rollback Failed")),
        ("suspend_in_progress", pgettext_lazy("current status of stack",
                                              u"Suspend In Progress")),
        ("suspend_complete", pgettext_lazy("current status of stack",
                                           u"Suspend Complete")),
        ("suspend_failed", pgettext_lazy("current status of stack",
                                         u"Suspend Failed")),
        ("resume_in_progress", pgettext_lazy("current status of stack",
                                             u"Resume In Progress")),
        ("resume_complete", pgettext_lazy("current status of stack",
                                          u"Resume Complete")),
        ("resume_failed", pgettext_lazy("current status of stack",
                                        u"Resume Failed")),
        ("adopt_in_progress", pgettext_lazy("current status of stack",
                                            u"Adopt In Progress")),
        ("adopt_complete", pgettext_lazy("current status of stack",
                                         u"Adopt Complete")),
        ("adopt_failed", pgettext_lazy("current status of stack",
                                       u"Adopt Failed")),
        ("snapshot_in_progress", pgettext_lazy("current status of stack",
                                               u"Snapshot In Progress")),
        ("snapshot_complete", pgettext_lazy("current status of stack",
                                            u"Snapshot Complete")),
        ("snapshot_failed", pgettext_lazy("current status of stack",
                                          u"Snapshot Failed")),
        ("check_in_progress", pgettext_lazy("current status of stack",
                                            u"Check In Progress")),
        ("check_complete", pgettext_lazy("current status of stack",
                                         u"Check Complete")),
        ("check_failed", pgettext_lazy("current status of stack",
                                       u"Check Failed")),
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
                           status=True,
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
        row_class = StacksUpdateRow
        table_actions = (common_actions.CreateClonePlanWithMulRes,
                         common_actions.CreateMigratePlanWithMulRes,)
        row_actions = (CloneStack,
                       MigrateStack,)
