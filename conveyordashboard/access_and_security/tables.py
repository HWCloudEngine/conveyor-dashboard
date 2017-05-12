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
from openstack_dashboard.dashboards.project.access_and_security.\
    floating_ips import tables as fip_tables
from openstack_dashboard.dashboards.project.access_and_security.\
    security_groups import tables as secgroup_tables

from conveyordashboard.common import actions as common_actions
from conveyordashboard.common import constants as consts


class CloneSecurityGroup(common_actions.CreateClonePlan):
    """"""


class MigrateSecurityGroup(common_actions.CreateMigratePlan):
    """"""


class SecurityGroupsTable(secgroup_tables.SecurityGroupsTable):
    class Meta(object):
        name = 'security_groups'
        verbose_name = _("Security Groups")
        css_classes = "table-res %s" % consts.NEUTRON_SECGROUP
        table_actions = (common_actions.CreateClonePlanWithMulRes,
                         common_actions.CreateMigratePlanWithMulRes)
        row_actions = (CloneSecurityGroup,
                       MigrateSecurityGroup,)


class CloneFloatingIP(common_actions.CreateClonePlan):
    """"""


class MigrateFloatingIP(common_actions.CreateMigratePlan):
    """"""


class FloatingIPsTable(fip_tables.FloatingIPsTable):
    ip = tables.Column("floating_ip_address",
                       verbose_name=_("IP Address"),
                       attrs={'data-type': "ip"})
    fixed_ip = tables.Column('fixed_ip_address',
                             verbose_name=_("Mapped Fixed IP Address"))
    pool = tables.Column("floating_network_id",
                         verbose_name=_("Pool"))

    def get_object_display(self, datum):
        return datum.floating_ip_address

    class Meta(object):
        name = 'floating_ips'
        verbose_name = _("Floating IPs")
        css_classes = "table-res %s" % consts.NEUTRON_FLOATINGIP
        table_actions = (common_actions.CreateClonePlanWithMulRes,
                         common_actions.CreateMigratePlanWithMulRes)
        row_actions = (CloneFloatingIP,
                       MigrateFloatingIP,)
