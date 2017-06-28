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

ALLOW_CLONE_STATUS = ('available', 'cloning', 'finished')
ALLOW_MIGRATE_STATUS = ('available', 'migrating', 'finished')
ALLOW_MODIFY_STATUS = ('initiating', 'available', 'finished')
NOT_ALLOW_EXPORT_STATUS = ('creating', 'error', 'initiating')


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, plan_id):
        plan = api.plan_get_brief(request, plan_id)
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


class ModifyPlan(tables.LinkAction):
    name = 'modify'
    verbose_name = _("Modify")
    url = 'horizon:conveyor:plans:modify'
    classes = ("ajax-modal",)

    def allowed(self, request, plan):
        return (plan.plan_type == 'clone'
                and plan.plan_status in ALLOW_MODIFY_STATUS)


class ClonePlan(tables.LinkAction):
    name = 'clone'
    verbose_name = _("Clone")
    url = 'horizon:conveyor:plans:clone'
    classes = ("ajax-modal", "btn-default", "btn-clone")
    help_text = _("Execute clone plan")

    def allowed(self, request, plan):
        return (plan.plan_type == 'clone'
                and plan.plan_status in ALLOW_CLONE_STATUS)

    def get_link_url(self, datum):
        base_url = reverse(self.url)
        params = urlencode({'plan_id': self.table.get_object_id(datum),
                            'type': 'clone'})
        return '?'.join([base_url, params])


class MigratePlan(tables.LinkAction):
    name = 'migrate'
    verbose_name = _("Migrate")
    url = 'horizon:conveyor:plans:migrate'
    classes = ("ajax-modal", "btn-default", "btn-migrate")
    help_text = _("Execute migrate plan")

    def get_link_url(self, datum):
        base_url = reverse(self.url)
        params = urlencode({'plan_id': self.table.get_object_id(datum),
                            'type': 'migrate'})
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


class GenerateTemplate(tables.BatchAction):
    name = 'generate_template'

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Generate Template",
            u"Generate Templates",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Generated Template",
            u"Generated Templates",
            count
        )

    def allowed(self, request, plan):
        return plan.plan_status in ('initiating',)

    def action(self, request, obj_id):
        plan = api.plan_get_brief(request, obj_id)
        if plan.plan_type == 'clone':
            api.export_clone_template(request, obj_id)
        elif plan.plan_type == 'migrate':
            api.export_migrate_template(request, obj_id)
        else:
            raise Exception("Unknown plan type %s" % plan.plan_type)


class CreateIncrementalClone(tables.LinkAction):
    name = 'create_incremental_clone'
    verbose_name = _("Create Incremental Clone")
    url = 'horizon:conveyor:plans:incremental_clone'
    classes = ("ajax-modal", "btn-default")

    def allowed(self, request, plan):
        if plan.plan_status != 'finished':
            return False
        plan_level = getattr(plan, 'plan_level', '')
        if plan_level:
            if plan_level.split(':')[0] in ('project', 'availability_zone'):
                return True
        return False


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
    plan_level = tables.Column("plan_level",
                               verbose_name=_("Plan Level"))
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

    def get_object_id(self, obj):
        return obj.plan_id

    class Meta(object):
        name = 'plans'
        verbose_name = _("Plans")
        status_columns = ["plan_status", ]
        table_actions = (ImportPlan, DeletePlan, PlanFilterAction)
        row_class = UpdateRow
        row_actions = (ClonePlan, MigratePlan, GenerateTemplate,
                       ModifyPlan, CreateIncrementalClone,
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
    url = 'horizon:conveyor:plans:local_topology'
    classes = ("ajax-modal",)

    def get_link_url(self, datum):
        base_url = reverse(self.url)
        params = urlencode({'res_id': self.table.get_object_id(datum),
                            'plan_id': self.table.kwargs['plan_id'],
                            'plan_type': self.table.kwargs['plan_type']})
        return '?'.join([base_url, params])

    def allowed(self, request, instance=None):
        """Allow terminate action if instance not currently being deleted."""
        return True


class GlobalTopology(tables.LinkAction):
    name = 'global_topology'
    verbose_name = _("Global Topology")
    url = 'horizon:conveyor:plans:global_topology'
    classes = ("ajax-modal",)

    def get_link_url(self, datum=None):
        base_url = reverse(self.url)
        params = urlencode({'plan_type': self.table.kwargs['plan_type'],
                            'plan_id': self.table.kwargs['plan_id']})
        return '?'.join([base_url, params])


def get_dep_name(dep):
    name = dep.name
    if not name:
        return '-'
    if len(name) > 36:
        return name[:33] + '...'
    return name


def trans_plan_deps(plan_deps):
    deps = []
    for dep in plan_deps.values():
        deps.append(models.Resource(dep))
    return deps


class PlanDepsTable(tables.DataTable):
    name = tables.Column(get_dep_name, verbose_name=_("Name"), sortable=False)
    res_id = tables.Column('name_in_template', verbose_name=_("Resource ID"),
                           sortable=False)
    res_type = tables.Column('type', verbose_name=_("Resource Type"),
                             sortable=False)

    def get_object_id(self, obj):
        return obj.name_in_template

    class Meta(object):
        name = 'plan_deps'
        verbose_name = _("Plan Deps")
        row_actions = (LocalTopology,)
        table_actions = (GlobalTopology,)
