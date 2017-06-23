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
from horizon import views
from oslo_log import log as logging

from conveyordashboard.api import api
from conveyordashboard.api import models
from conveyordashboard.common import constants as consts
from conveyordashboard.common import tables as conveyor_table
from conveyordashboard.overview_project import tables as overview_tables

LOG = logging.getLogger(__name__)


class IndexView(views.HorizonTemplateView,
                conveyor_table.FilterTableMixin):
    page_title = _("Overview")
    template_name = 'overview_project/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)

        data = []
        data.extend(self.get_instances_data())
        data.extend(self.get_volumes_data())
        data.extend(self.get_networks_data())
        data.extend(self.get_floating_ips_data())
        data.extend(self.get_security_groups_data())
        data.extend(self.get_pools_data())
        data.extend(self.get_stacks_data())

        context['table'] = overview_tables.ResTable(self.request, data=data)
        return context

    def get_instances_data(self):
        try:
            res = []
            instances = api.resource_list(self.request, consts.NOVA_SERVER)
            for i in filter(self._instance_status_filter, instances):
                res.append(models.OverviewResource({
                    'res_id': i.id,
                    'res_type': consts.NOVA_SERVER,
                    'name': i.name
                }))
            return res
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve instances list."))
            return []

    def get_volumes_data(self):
        try:
            res = []
            volumes = api.resource_list(self.request, consts.CINDER_VOLUME)
            for vol in filter(self._volume_status_filter, volumes):
                res.append(models.OverviewResource({
                    'res_id': vol.id,
                    'res_type': consts.CINDER_VOLUME,
                    'name': vol.display_name or vol.id
                }))
            return res
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve volumes list."))
            return []

    def get_networks_data(self):
        try:
            res = []
            nets = api.net_list_for_tenant(self.request,
                                           self.request.user.tenant_id)
            for net in filter(self._network_status_filter, nets):
                res.append(models.OverviewResource({
                    'res_id': net.id,
                    'res_type': consts.NEUTRON_NET,
                    'name': net.name
                }))
            return res
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve network list."))
            return []

    def get_security_groups_data(self):
        try:
            res = []
            secgroups = api.sg_list(self.request, self.request.user.tenant_id)
            for sg in sorted(secgroups, key=lambda group: group.name):
                res.append(models.OverviewResource({
                    'res_id': sg.id,
                    'res_type': consts.NEUTRON_SECGROUP,
                    'name': sg.name
                }))
            return res
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve security groups.'))
            return []

    def get_floating_ips_data(self):
        try:
            res = []
            fips = api.resource_list(self.request, consts.NEUTRON_FLOATINGIP)
            for fip in fips:
                res.append(models.OverviewResource({
                    'res_id': fip.id,
                    'res_type': consts.NEUTRON_FLOATINGIP,
                    'name': fip.floating_ip_address
                }))
            return res
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve floating IP addresses.'))
            return []

    def get_pools_data(self):
        try:
            res = []
            pools = api.resource_list(self.request, consts.NEUTRON_POOL)
            for pool in pools:
                res.append(models.OverviewResource({
                    'res_id': pool.id,
                    'res_type': consts.NEUTRON_POOL,
                    'name': pool.name
                }))
            return res
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve pools list.'))
            return []

    def get_stacks_data(self):
        try:
            res = []
            stacks = api.stack_list(self.request)
            for stack in stacks:
                res.append(models.OverviewResource({
                    'res_id': stack.id,
                    'res_type': consts.HEAT_STACK,
                    'name': stack.stack_name
                }))
            return res
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve stacks."))
            return []
