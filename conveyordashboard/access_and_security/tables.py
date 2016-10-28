# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
# Copyright 2012 OpenStack Foundation
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
    floating_ips.tables import FloatingIPsTable
from openstack_dashboard.dashboards.project.access_and_security.\
    security_groups.tables import SecurityGroupsTable

from conveyordashboard.overview import tables as overview_tables


class SecurityGroupsTable(SecurityGroupsTable):
    class Meta(object):
        name = 'security_groups'
        verbose_name = _("Security Groups")
        css_classes = "table-res OS::Neutron::SecurityGroup"
        table_actions = (overview_tables.CreatePlanWithMulRes,
                         overview_tables.CreateMigratePlanWithMulRes)
        row_actions = (overview_tables.CreateClonePlan,
                       overview_tables.CreateMigratePlan,)


class FloatingIPsTable(FloatingIPsTable):
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
        css_classes = "table-res OS::Neutron::FloatingIP"
        table_actions = (overview_tables.CreatePlanWithMulRes,
                         overview_tables.CreateMigratePlanWithMulRes)
        row_actions = (overview_tables.CreateClonePlan,
                       overview_tables.CreateMigratePlan,)
