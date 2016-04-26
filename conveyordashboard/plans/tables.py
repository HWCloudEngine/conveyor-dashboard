import datetime
import logging

from django.core.urlresolvers import reverse
from django.template.defaultfilters import title  # noqa
from django.utils.http import urlencode
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import messages
from horizon import tables
from horizon.utils import filters

from openstack_dashboard import policy

from conveyordashboard.api import api

LOG = logging.getLogger(__name__)

PLAN_ALLOW_CLONE_STATUS = ('available',)


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, plan_id):
        try:
            plan = api.plan_get(request, plan_id)
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve plan information '
                                '"%s".') % plan_id,
                              ignore=True)
        return plan


class DeletePlan(tables.BatchAction):
    name = "delete"
    classes = ("btn-default", "btn-danger",)
    icon = "remove"
    help_text = _("Delete clone plan is not recoverable.")

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
            u"Scheduled deleting of Clone Plan",
            u"Scheduled deleting of Clone Plan",
            count
        )

    def allowed(self, request, instance=None):
        """Allow terminate action if instance not currently being deleted."""
        return True

    def action(self, request, obj_id):
        api.plan_delete(request, obj_id)


def is_expired(plan):
    UTC_FORMAT = '%Y-%m-%dT%H:%M:%S.%f'
    return datetime.datetime.utcnow().strftime(UTC_FORMAT) > plan.expire_at

ALLOW_CLONE_STATUS = ('available', 'finished', 'expired')
ALLOW_MIGRATE_STATUS = ('available', 'finished')
NOT_ALLOW_EXPORT_STATUS = ('expired',)


class ClonePlan(policy.PolicyTargetMixin, tables.LinkAction):
    name = "clone"
    verbose_name = _("Clone")
    url = "horizon:conveyor:overview:create_plan"
    classes = ("ajax-modal", "btn-default", "btn-clone")
    help_text = _("Execute clone plan")

    def allowed(self, request, plan):
        return (plan.plan_type == "clone"
                and plan.plan_status in ALLOW_CLONE_STATUS)

    def get_link_url(self, datum):
        base_url = reverse(self.url)
        params = urlencode({"plan_id": self.table.get_object_id(datum),
                            "type": "clone",
                            "next_url": self.table.get_full_url()})
        return "?".join([base_url, params])


class MigratePlan(tables.LinkAction):
    name = "migrate"
    verbose_name = _("Migrate")
    url = "horizon:conveyor:overview:create_plan"
    classes = ("ajax-modal", "btn-default", "btn-clone")
    help_text = _("Execute migrate plan")

    def get_link_url(self, datum):
        base_url = reverse(self.url)
        params = urlencode({"plan_id": self.table.get_object_id(datum),
                            "type": "migrate",
                            "next_url": self.table.get_full_url()})
        return "?".join([base_url, params])

    def allowed(self, request, plan):
        return (plan.plan_type == "migrate"
                and plan.plan_status in ALLOW_MIGRATE_STATUS)


class ImportPlan(policy.PolicyTargetMixin, tables.LinkAction):
    name = "import"
    verbose_name = _("Import")
    url = "horizon:conveyor:plans:import"
    icon = "upload"
    classes = ("ajax-modal", "btn-default", "btn-import")
    help_text = _("Import clone plan from local")


class ExportPlan(policy.PolicyTargetMixin, tables.LinkAction):
    name = "export"
    verbose_name = _("Export")
    url = "horizon:conveyor:plans:export"
    icon = "download"
    classes = ("ajax-modal", "btn-default", "btn-export")
    help_text = _("Export clone plan.")

    def allowed(self, request, plan):
        return plan.plan_status not in ('expired',)


class CreateTrigger(policy.PolicyTargetMixin, tables.LinkAction):
    name = "create_trigger"
    verbose_name = _("Create Trigger")
    url = "horizon:conveyor:plans:create_trigger"
    icon = "download"
    classes = ("ajax-modal", "btn-default", "btn-trigger")
    help_text = _("Creating trigger for clone plan.")

    def allowed(self, request, plan):
        return plan.plan_status not in ('expired',)


class PlanFilterAction(tables.FilterAction):
    name = "filter_clone_plan"
    filter_type = "plan"
    filter_choices = (('project', _("Project"), True),
                      ('name', _("Name"), True),)


STATUS_DISPLAY_CHOICES = (
    ("initiating", "Initiating"),
    ("creating", "Creating"),
    ("available", "Available"),
    ("cloning", "Cloning"),
    ("migrating", "Migrating"),
    ("finished", "Finished"),
    ("deleting", "Deleting"),
    ("deleted", "Deleted"),
    ("expired", "Expired"),
    ("error", "Error"),
    ("error_deleting", "error_deleting")
)

TASK_DISPLAY_NONE = "None"

TASK_DISPLAY_CHOICES = (
    ("deploying", "Deploying"),
    ("finished", "Finished"),
    ("failed", "Failed"),
)


class PlanTable(tables.DataTable):
    PLAN_STATUS_CHOICES=(
        ('initiating', True),
        ('available', True),
        ('error', False),
        ('finished', True),
        ('expired', True))
    TASK_STATUS_CHOICES = (
        (None, True),
        ("none", True),
        ("", True),
    )
    # NOTE(gabriel): Commenting out the user column because all we have
    # is an ID, and correlating that at production scale using our current
    # techniques isn't practical. It can be added back in when we have names
    # returned in a practical manner by the API.
    plan_id = tables.Column("plan_id",
                            link="horizon:conveyor:plans:detail",
                            verbose_name=_("Plan Id"))
    plan_type = tables.Column("plan_type",
                              verbose_name=_("Plan Type"))
    created = tables.Column("created_at",
                            verbose_name=_("Create Time"))
    expire = tables.Column("expire_at",
                           verbose_name=_("Expire Time"))
    plan_status = tables.Column("plan_status",
                                filters=(title, filters.replace_underscores),
                                verbose_name=_("Plan Status"),
                                status=True,
                                status_choices=PLAN_STATUS_CHOICES,
                                display_choices=STATUS_DISPLAY_CHOICES)
    task_status = tables.Column("task_status",
                                verbose_name=_("Task Status"),
                                status=True,
                                empty_value=TASK_DISPLAY_NONE,
                                status_choices=TASK_STATUS_CHOICES,
                                display_choices=TASK_DISPLAY_CHOICES)

    def get_object_id(self, obj):
        return obj.plan_id

    class Meta(object):
        name = "plans"
        verbose_name = _("Plans")
        status_columns = ["plan_status", "task_status"]
        table_actions = (ImportPlan, DeletePlan,
                         PlanFilterAction)
        row_class = UpdateRow
        row_actions = (DeletePlan, ClonePlan, MigratePlan, ExportPlan,
                       CreateTrigger,)
