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

from django import template
from django.template.defaultfilters import title  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables
from horizon.templatetags import sizeformat
from horizon.utils import filters

from openstack_dashboard import api as openstack_api
from openstack_dashboard.dashboards.project.instances \
    import tables as project_tables

from conveyordashboard.api import api
from conveyordashboard.common import actions as common_actions
from conveyordashboard.common import constants as consts
from conveyordashboard.common import resource_state


def get_property(obj, key, default=None):
    try:
        return getattr(obj, key, default)
    except AttributeError:
        return obj.get(key, default)


def get_size(instance):
    if hasattr(instance, 'full_flavor'):
        template_name = 'project/instances/_instance_flavor.html'
        f = instance.full_flavor
        size_ram = sizeformat.mb_float_format(get_property(f, 'ram'))
        if get_property(f, 'disk') > 0:
            size_disk = sizeformat.diskgbformat(get_property(f, 'disk'))
        else:
            size_disk = _("%s GB") % "0"
        context = {
            'name': get_property(f, 'name'),
            'id': instance.id,
            'size_disk': size_disk,
            'size_ram': size_ram,
            'vcpus': get_property(f, 'vcpus'),
            'flavor_id': get_property(f, 'id')
        }
        return template.loader.render_to_string(template_name, context)
    return _("Not available")


class CloneInstance(common_actions.CreateClonePlan):
    def allowed(self, request, instance=None):
        """Allow terminate action if instance not currently being deleted."""
        if not instance:
            return True
        return (instance.status in resource_state.INSTANCE_CLONE_STATE) \
            and not project_tables.is_deleting(instance)


class MigrateInstance(common_actions.CreateMigratePlan):
    def allowed(self, request, instance=None):
        """Allow terminate action if instance not currently being deleted."""
        if not instance:
            return True
        return (instance.status in resource_state.INSTANCE_MIGRATE_STATE) \
            and not project_tables.is_deleting(instance)


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, instance_id):
        instance = api.server_get(request, instance_id)
        try:
            instance.full_flavor = api.flavor_get(request,
                                                  instance.flavor['id'])
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve flavor information '
                                'for instance "%s".') % instance_id,
                              ignore=True)

        try:
            openstack_api.network.servers_update_addresses(request, [instance])
        except Exception:
            exceptions.handle(request,
                              _('Unable to retrieve Network information '
                                'for instance "%s".') % instance_id,
                              ignore=True)
        return instance


class InstanceFilterAction(tables.FilterAction):
    # Change default name of 'filter' to distinguish this one from the
    # project instances table filter, since this is used as part of the
    # session property used for persisting the filter.
    name = 'filter_clone_instances'
    filter_type = 'server'
    filter_choices = (('name', _("Instance Name"), True),
                      ('status', _("Status ="), True),
                      ('image', _("Image ID ="), True),
                      ('flavor', _("Flavor ID ="), True))


class InstancesTable(tables.DataTable):
    TASK_STATUS_CHOICES = (
        (None, True),
        ("none", True)
    )
    STATUS_CHOICES = (
        ("active", True),
        ("shutoff", True),
        ("suspended", True),
        ("paused", True),
        ("error", False),
        ("rescue", True),
        ("shelved", True),
        ("shelved_offloaded", True),
    )
    # NOTE(gabriel): Commenting out the user column because all we have
    # is an ID, and correlating that at production scale using our current
    # techniques isn't practical. It can be added back in when we have names
    # returned in a practical manner by the API.
    # user = tables.Column("user_id", verbose_name=_("User"))
    name = tables.Column("name",
                         link="horizon:admin:instances:detail",
                         verbose_name=_("Name"))
    image_name = tables.Column("image_name",
                               verbose_name=_("Image Name"))
    ip = tables.Column(project_tables.get_ips,
                       verbose_name=_("IP Address"),
                       attrs={'data-type': "ip"})
    size = tables.Column(get_size,
                         verbose_name=_("Size"),
                         attrs={'data-type': 'size'})
    status = tables.Column(
        "status",
        filters=(title, filters.replace_underscores),
        verbose_name=_("Status"),
        status=True,
        status_choices=STATUS_CHOICES,
        display_choices=project_tables.STATUS_DISPLAY_CHOICES)
    task = tables.Column("OS-EXT-STS:task_state",
                         verbose_name=_("Task"),
                         empty_value=project_tables.TASK_DISPLAY_NONE,
                         status=True,
                         status_choices=TASK_STATUS_CHOICES,
                         display_choices=project_tables.TASK_DISPLAY_CHOICES)
    state = tables.Column(project_tables.get_power_state,
                          filters=(title, filters.replace_underscores),
                          verbose_name=_("Power State"),
                          display_choices=project_tables.POWER_DISPLAY_CHOICES)

    class Meta(object):
        name = 'instances'
        css_classes = "table-res %s" % consts.NOVA_SERVER
        verbose_name = _("Instances")
        status_columns = ['status', 'task']
        res_type = consts.NOVA_SERVER
        table_actions = (common_actions.CreateClonePlanWithMulRes,
                         common_actions.CreateMigratePlanWithMulRes,
                         InstanceFilterAction)
        row_class = UpdateRow
        row_actions = (project_tables.ConfirmResize,
                       CloneInstance,
                       MigrateInstance,)
