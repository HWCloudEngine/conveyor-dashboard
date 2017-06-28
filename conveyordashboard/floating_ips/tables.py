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

from conveyordashboard.common import actions as common_actions
from conveyordashboard.common import constants as consts


class CreatePlan(common_actions.CreatePlan):
    """"""


STATUS_DISPLAY_CHOICES = (
    ("active", pgettext_lazy("Current status of a Floating IP", u"Active")),
    ("down", pgettext_lazy("Current status of a Floating IP", u"Down")),
    ("error", pgettext_lazy("Current status of a Floating IP", u"Error")),
)


class FloatingIPsTable(tables.DataTable):
    STATUS_CHOICES = (
        ("active", True),
        ("down", True),
        ("error", False)
    )
    ip = tables.Column("floating_ip_address",
                       verbose_name=_("IP Address"),
                       attrs={'data-type': "ip"})
    fixed_ip = tables.Column('fixed_ip_address',
                             verbose_name=_("Mapped Fixed IP Address"))
    pool = tables.Column("floating_network_id",
                         verbose_name=_("Pool"))
    status = tables.Column("status",
                           verbose_name=_("Status"),
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)

    def get_object_display(self, datum):
        return datum.floating_ip_address

    class Meta(object):
        name = 'floating_ips'
        verbose_name = _("Floating IPs")
        css_classes = "table-res %s" % consts.NEUTRON_FLOATINGIP
        table_actions = (common_actions.CreatePlanWithMultiRes,)
        row_actions = (CreatePlan,)
