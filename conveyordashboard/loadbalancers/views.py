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
from horizon import tables
from openstack_dashboard import api as os_api

from conveyordashboard.api import api
from conveyordashboard.common import constants as consts
from conveyordashboard.common import resource_state
from conveyordashboard.loadbalancers import tables as lb_tables


class IndexView(tables.DataTableView):
    table_class = lb_tables.PoolsTable
    template_name = '_res_table.html'
    page_title = _("Pools")

    def get_data(self):
        pools = []
        try:
            request = self.request
            pools = api.resource_list(request, consts.NEUTRON_POOL)[0].pools
            pools = [os_api.lbaas.Pool(p) for p in pools]
            fips = None
            for pool in pools:
                if hasattr(pool, "vip") and pool.vip:
                    if not fips:
                        fips = api.resource_list(self.request,
                                                 consts.NEUTRON_FLOATINGIP)
                    vip_fip = [fip for fip in fips
                               if fip.port_id == pool.vip.port_id]
                    if vip_fip:
                        pool.vip.fip = vip_fip[0]
            pools = filter(self._status_filter, pools)
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve pools list.'))
        return pools

    def _status_filter(self, pool):
        return pool.status in resource_state.POOL_CLONE_STATE
