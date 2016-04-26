# Copyright 2012 OpenStack Foundation
# Copyright 2012 Nebula, Inc.
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
import logging

from django import template
from django.conf import settings
from django.core import urlresolvers
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.template.defaultfilters import title  # noqa
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

import six

from horizon import tables
from horizon import exceptions
from horizon import messages
from horizon.templatetags import sizeformat
from horizon.utils import filters

from openstack_dashboard import api as openstack_api
from openstack_dashboard.dashboards.project.instances \
    import tables as project_tables
from openstack_dashboard import policy
from conveyordashboard.api import api
from conveyordashboard.overview import tables as overview_tables

LOG = logging.getLogger(__name__)

CLONE_ALLOWED_STATUS = ("SHUTOFF",)


def filter_direction(direction):
    if direction is None or direction.lower() == 'ingress':
        return _('Ingress')
    else:
        return _('Egress')


def filter_protocol(protocol):
    if protocol is None:
        return _('Any')
    return six.text_type.upper(protocol)


def get_remote_ip_prefix(rule):
    if 'cidr' in rule.ip_range:
        if rule.ip_range['cidr'] is None:
            range = '::/0' if rule.ethertype == 'IPv6' else '0.0.0.0/0'
        else:
            range = rule.ip_range['cidr']
        return range
    else:
        return None


def get_remote_security_group(rule):
    return rule.group.get('name')


def get_port_range(rule):
    # There is no case where from_port is None and to_port has a value,
    # so it is enough to check only from_port.
    if rule.from_port is None:
        return _('Any')
    ip_proto = rule.ip_protocol
    if rule.from_port == rule.to_port:
        return check_rule_template(rule.from_port, ip_proto)
    else:
        return (u"%(from)s - %(to)s" %
                {'from': check_rule_template(rule.from_port, ip_proto),
                 'to': check_rule_template(rule.to_port, ip_proto)})


def check_rule_template(port, ip_proto):
    rules_dict = getattr(settings, 'SECURITY_GROUP_RULES', {})
    if not rules_dict:
        return port
    templ_rule = [rule for rule in rules_dict.values()
                  if (str(port) == rule['from_port']
                      and str(port) == rule['to_port']
                      and ip_proto == rule['ip_protocol'])]
    if templ_rule:
        return u"%(from_port)s (%(name)s)" % templ_rule[0]
    return port


class CreateRule(tables.LinkAction):
    name = "add_rule"
    verbose_name = "Add Rule"
    classes = ("ajax-modal", "btn-add-rule",)
    icon = "plus"
    url = "javascript:void(0);"


class DeleteRule(tables.LinkAction):
    name = "delete_rule"
    verbose_name = "Delete Rule"
    classes = ("ajax-modal", "btn-delete-rule", "disabled")
    icon = "remove"
    url = "javascript:void(0);"


class RulesTable(tables.DataTable):
    direction = tables.Column("direction",
                              verbose_name=_("Direction"),
                              filters=(filter_direction,))
    ethertype = tables.Column("ethertype",
                              verbose_name=_("Ether Type"))
    protocol = tables.Column("ip_protocol",
                             verbose_name=_("IP Protocol"),
                             filters=(filter_protocol,))
    port_range = tables.Column(get_port_range,
                               verbose_name=_("Port Range"))
    remote_ip_prefix = tables.Column(get_remote_ip_prefix,
                                     verbose_name=_("Remote IP Prefix"))
    remote_security_group = tables.Column(get_remote_security_group,
                                          verbose_name=_("Remote Security"
                                                         " Group"))

    def sanitize_id(self, obj_id):
        return filters.get_int_or_uuid(obj_id)

    def get_object_display(self, rule):
        return six.text_type(rule)

    class Meta(object):
        name = "rules"
        verbose_name = _("Security Group Rules")
        table_actions = (CreateRule, DeleteRule,)


def get_property(obj, key, default=None):
    try:
        return getattr(obj, key, default)
    except AttributeError:
        return obj.get(key, default)
    raise TypeError


def get_size(instance):
    if hasattr(instance, "full_flavor"):
        template_name = 'project/instances/_instance_flavor.html'
        f = instance.full_flavor
        size_ram = sizeformat.mb_float_format(get_property(f, "ram"))
        if get_property(f, "disk") > 0:
            size_disk = sizeformat.diskgbformat(get_property(f, "disk"))
        else:
            size_disk = _("%s GB") % "0"
        context = {
            "name": get_property(f, "name"),
            "id": instance.id,
            "size_disk": size_disk,
            "size_ram": size_ram,
            "vcpus": get_property(f, "vcpus"),
            "flavor_id": get_property(f, "id")
        }
        return template.loader.render_to_string(template_name, context)
    return _("Not available")


class CreateInstancePlan(overview_tables.CreateClonePlan):
    def allowed(self, request, instance=None):
        """Allow terminate action if instance not currently being deleted."""
        if not instance: return True
        return ((instance.status in CLONE_ALLOWED_STATUS)
                and not project_tables.is_deleting(instance))


class UpdateRow(tables.Row):
    ajax = True

    def get_data(self, request, instance_id):
        try:
            instance = api.server_get(request, instance_id)
            instance.full_flavor = api.flavor_get(request,
                                                  instance.flavor["id"])
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
    name = "filter_clone_instances"
    filter_type = "server"
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
        name = "instances"
        css_classes = "table-res OS::Nova::Server"
        verbose_name = _("Instances")
        status_columns = ["status", "task"]
        res_type = "OS::Nova::Server"
        table_actions = (overview_tables.CreatePlanWithMulRes,
                         overview_tables.CreateMigratePlanWithMulRes,
                         InstanceFilterAction)
        row_class = UpdateRow
        row_actions = (project_tables.ConfirmResize,
                       overview_tables.CreateClonePlan,
                       overview_tables.CreateMigratePlan,)
