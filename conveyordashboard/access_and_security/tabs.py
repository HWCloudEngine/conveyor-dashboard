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

from horizon import exceptions
from horizon import tabs
from oslo_log import log as logging

from conveyordashboard.access_and_security import tables as conveyor_table
from conveyordashboard.api import api
from conveyordashboard.common import constants as consts

LOG = logging.getLogger(__name__)


class SecurityGroupsTab(tabs.TableTab):
    table_classes = (conveyor_table.SecurityGroupsTable,)
    name = _("Security Groups")
    slug = "security_groups_tab"
    template_name = "horizon/common/_detail_table.html"
    permissions = ('openstack.services.compute',)

    def get_security_groups_data(self):
        try:
            secgroups = api.sg_list(self.request, self.request.user.tenant_id)
        except Exception:
            secgroups = []
            exceptions.handle(self.request,
                              _('Unable to retrieve security groups.'))
        return sorted(secgroups, key=lambda group: group.name)


class FloatingIPsTab(tabs.TableTab):
    table_classes = (conveyor_table.FloatingIPsTable,)
    name = _("Floating IPs")
    slug = "floating_ips_tab"
    template_name = "horizon/common/_detail_table.html"
    permissions = ('openstack.services.compute',)

    def get_floating_ips_data(self):
        try:
            fips = api.resource_list(self.request, consts.NEUTRON_FLOATINGIP)
            LOG.info("a&s fips: %s", [ip.__dict__ for ip in fips])
        except Exception:
            fips = []
            exceptions.handle(self.request,
                              _('Unable to retrieve floating IP addresses.'))
        return fips
        # try:
        #     floating_ip_pools = network.floating_ip_pools_list(self.request)
        # except neutron_exc.ConnectionFailed:
        #     floating_ip_pools = []
        #     exceptions.handle(self.request)
        # except Exception:
        #     floating_ip_pools = []
        #     exceptions.handle(self.request,
        #                       _('Unable to retrieve floating IP pools.'))
        # pool_dict = dict([(obj.id, obj.name) for obj in floating_ip_pools])

        attached_instance_ids = [ip.instance_id for ip in fips
                                 if ip.instance_id is not None]
        if attached_instance_ids:
            instances = []
            try:
                # TODO(tsufiev): we should pass attached_instance_ids to
                # nova.server_list as soon as Nova API allows for this
                instances, has_more = api.server_list(self.request)
            except Exception:
                exceptions.handle(self.request,
                                  _('Unable to retrieve instance list.'))

            instances_dict = dict([(obj.id, obj.name) for obj in instances])

            for ip in fips:
                ip.instance_name = instances_dict.get(ip.instance_id)
                # ip.pool_name = pool_dict.get(ip.pool, ip.pool)

        return fips


class AccessAndSecurityTabs(tabs.TabGroup):
    slug = "access_security_tabs"
    tabs = (SecurityGroupsTab, FloatingIPsTab)
    sticky = True
