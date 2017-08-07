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
from django.template.defaultfilters import title  # noqa
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables
from horizon.utils import filters
from oslo_log import log as logging

from conveyordashboard.api import api
from conveyordashboard.api import models
from conveyordashboard.common import utils

LOG = logging.getLogger(__name__)

ALLOW_CLONE_STATUS = ('available', 'finished')
ALLOW_MIGRATE_STATUS = ('available', 'finished')
NOT_ALLOW_EXPORT_STATUS = ('available', 'cloning', 'migrating', 'finished')


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, plan_id):
        plan = api.plan_get(request, plan_id)
        return plan


class DeletePlan(tables.DeleteAction):
    help_text = _("Delete plan is not recoverable.")

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Plan",
            u"Delete Plans",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Scheduled deletion of Plan",
            u"Scheduled deletion of Plans",
            count
        )

    def allowed(self, request, plan=None):
        return True

    def action(self, request, obj_id):
        api.plan_delete(request, obj_id)


class ClonePlan(tables.LinkAction):
    name = 'clone'
    verbose_name = _("Clone")
    url = 'horizon:conveyor:plans:destination'
    classes = ("ajax-modal", "btn-default", "btn-clone")

    def allowed(self, request, plan):
        return (plan.plan_type == 'clone'
                and plan.plan_status in ALLOW_CLONE_STATUS)

    def get_link_url(self, datum):
        base_url = reverse(self.url,
                           kwargs={'plan_id': self.table.get_object_id(datum)})
        params = urlencode({'type': 'clone'})
        return '?'.join([base_url, params])


class MigratePlan(tables.LinkAction):
    name = 'migrate'
    verbose_name = _("Migrate")
    url = 'horizon:conveyor:plans:destination'
    classes = ("ajax-modal", "btn-default", "btn-migrate")

    def get_link_url(self, datum):
        base_url = reverse(self.url,
                           kwargs={'plan_id': self.table.get_object_id(datum)})
        params = urlencode({'type': 'migrate'})
        return '?'.join([base_url, params])

    def allowed(self, request, plan):
        return (plan.plan_type == 'migrate'
                and plan.plan_status in ALLOW_MIGRATE_STATUS)


class ImportPlan(tables.LinkAction):
    name = 'import'
    verbose_name = _("Import")
    url = 'horizon:conveyor:plans:import'
    icon = 'upload'
    classes = ("ajax-modal", "btn-default", "btn-import")
    help_text = _("Import plan from local")


class ExportPlan(tables.LinkAction):
    name = 'export'
    verbose_name = _("Download")
    icon = 'download'
    url = 'horizon:conveyor:plans:export'

    def allowed(self, request, plan):
        return plan.plan_status not in NOT_ALLOW_EXPORT_STATUS


class PlanFilterAction(tables.FilterAction):
    def filter(self, table, plans, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [plan for plan in plans
                if query in getattr(plan, 'name', '').lower()]


PLAN_TYPE_CHOICES = (
    ("clone", gettext_lazy(u"Clone")),
    ("migrate", gettext_lazy(u"Migrate"))
)

STATUS_DISPLAY_CHOICES = (
    ("initiating", pgettext_lazy("Current status of plan", u"Initiating")),
    ("creating", pgettext_lazy("Current status of plan", u"Creating")),
    ("available", pgettext_lazy("Current status of plan", u"Available")),
    ("cloning", pgettext_lazy("Current status of plan", u"Cloning")),
    ("migrating", pgettext_lazy("Current status of plan", u"Migrating")),
    ("finished", pgettext_lazy("Current status of plan", u"Finished")),
    ("deleting", pgettext_lazy("Current status of plan", u"Deleting")),
    ("deleted", pgettext_lazy("Current status of plan", u"Deleted")),
    ("error", pgettext_lazy("Current status of plan", u"Error")),
    ("error_deleting",
     pgettext_lazy("Current status of plan", u"Error Deleting")),
)

TASK_DISPLAY_NONE = pgettext_lazy("Task status of plan", u"None")

TASK_DISPLAY_CHOICES = (
    ("deploying", pgettext_lazy("Task status of plan", u"Deploying")),
    ("finished", pgettext_lazy("Task status of plan", u"Finished")),
    ("failed", pgettext_lazy("Task status of plan", u"Failed")),
)


class PlansTable(tables.DataTable):
    PLAN_STATUS_CHOICES = (
        ('available', True),
        ('error', False),
        ('finished', True))
    TASK_STATUS_CHOICES = (
        (None, True),
        ('none', True),
        ('', True),
    )
    # NOTE(gabriel): Commenting out the user column because all we have
    # is an ID, and correlating that at production scale using our current
    # techniques isn't practical. It can be added back in when we have names
    # returned in a practical manner by the API.
    plan_name = tables.Column("plan_name",
                              link="horizon:conveyor:plans:detail",
                              verbose_name=_("Plan Name"))
    plan_type = tables.Column("plan_type",
                              filters=(title,),
                              verbose_name=_("Plan Type"),
                              display_choices=PLAN_TYPE_CHOICES)
    created = tables.Column("created_at",
                            verbose_name=_("Time since created"),
                            filters=(filters.parse_isotime,
                                     filters.timesince_sortable),
                            attrs={'data-type': 'timesince'})
    plan_status = tables.Column("plan_status",
                                filters=(title, filters.replace_underscores),
                                verbose_name=_("Plan Status"),
                                status=True,
                                status_choices=PLAN_STATUS_CHOICES,
                                display_choices=STATUS_DISPLAY_CHOICES)
    task_status = tables.Column("task_status",
                                verbose_name=_("Task Status"),
                                status=True,
                                status_choices=TASK_STATUS_CHOICES,
                                display_choices=TASK_DISPLAY_CHOICES)

    class Meta(object):
        name = 'plans'
        verbose_name = _("Plans")
        status_columns = ["plan_status", ]
        table_actions = (ImportPlan, DeletePlan, PlanFilterAction)
        row_class = UpdateRow
        row_actions = (ClonePlan, MigratePlan,
                       ExportPlan, DeletePlan,)


def get_src_az_md5(availability_zone):
    return utils.md5(availability_zone.availability_zone)


class DestinationAZTable(tables.DataTable):
    src_az = tables.Column('availability_zone',
                           verbose_name=_("Source Availability Zone"))
    src_az_md5 = tables.Column(get_src_az_md5, hidden=True)
    dst_az = tables.Column('destination_availability_zone',
                           empty_value="",
                           verbose_name=_("Destination Availability Zone"))

    def get_object_id(self, obj):
        return obj.availability_zone

    class Meta(object):
        name = 'destination_az'
        verbose_name = _("Destination Availability Zone")


class LocalTopology(tables.LinkAction):
    name = 'local_topology'
    verbose_name = _("Local Topology")
    classes = ("ajax-modal",)

    def get_default_attrs(self):
        self.attrs.update({
            'plan_id': self.table.kwargs['plan_id'],
            'res_id': self.table.get_object_id(self.datum),
            'res_type': self.datum.type
        })
        return super(LocalTopology, self).get_default_attrs()

    def get_link_url(self, datum):
        return "javascript:void(0);"


class GlobalTopology(tables.LinkAction):
    name = 'global_topology'
    verbose_name = _("Global Topology")
    classes = ("ajax-modal",)

    def get_default_attrs(self):
        self.attrs.update({
            'plan_id': self.table.kwargs['plan_id']
        })
        return super(GlobalTopology, self).get_default_attrs()

    def get_link_url(self, datum=None):
        return "javascript:void(0);"


def get_dep_name(dep):
    name = dep.name_in_template
    if not name:
        return '-'
    if len(name) > 36:
        return name[:33] + '...'
    return name


def trans_plan_deps(plan_deps):
    deps = []
    for dep in plan_deps:
        deps.append(models.Resource(dep))
    return deps


class PlanDepsTable(tables.DataTable):
    name = tables.Column(get_dep_name, verbose_name=_("Name"), sortable=False)
    res_id = tables.Column('id', verbose_name=_("Resource ID"),
                           sortable=False)
    res_type = tables.Column('type', verbose_name=_("Resource Type"),
                             sortable=False)

    class Meta(object):
        name = 'plan_deps'
        verbose_name = _("Plan Dependencies")
        table_actions = (GlobalTopology,)
        row_actions = (LocalTopology,)
