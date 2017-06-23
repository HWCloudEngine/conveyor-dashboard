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

from openstack_dashboard import api as os_api

from conveyordashboard.api import api
from conveyordashboard.common import constants as consts
from conveyordashboard.overview import tables as overview_tables

LOG = logging.getLogger(__name__)


class Res(object):
    def __init__(self, project_id, res_id, res_type, name):
        self.project_id = project_id
        self.id = res_id
        self.res_type = res_type
        self.name = name


class IndexView(views.HorizonTemplateView):
    table_class = overview_tables.ResTable
    page_title = _("Overview")
    template_name = 'overview_project/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        res = dict()
        res[consts.NOVA_SERVER] = self.get_instances_data()
        res[consts.CINDER_VOLUME] = self.get_volumes_data()
        res[consts.NEUTRON_NET] = self.get_networks_data()
        res[consts.NEUTRON_SECGROUP] = self.get_security_groups_data()
        res[consts.NEUTRON_POOL] = self.get_pools_data()

        data = []
        tenant_name = self.request.user.tenant_name
        for k, v in res.items():
            if not len(v):
                continue
            else:
                for entry in v:
                    data.append(Res(tenant_name, entry.id, k, entry.name))
        context['table'] = overview_tables.ResTable(self.request,
                                                    data=data).render()
        return context

    def get_data(self):
        res = dict()
        res[consts.NOVA_SERVER] = self.get_instances_data()
        res[consts.CINDER_VOLUME] = self.get_volumes_data()
        res[consts.NEUTRON_NET] = self.get_networks_data()
        res[consts.NEUTRON_SECGROUP] = self.get_security_groups_data()
        res[consts.NEUTRON_POOL] = self.get_pools_data()

        data = []
        tenant_id = self.request.user.tenant_id
        for k, v in res.items():
            if not len(v):
                continue
            else:
                for entry in v:
                    data.append(Res(tenant_id, entry.id, k, entry.name))
        LOG.info('Res: %s', data)
        return data

    def get_instances_data(self):
        instances = []
        try:
            instances = api.resource_list(self.request, consts.NOVA_SERVER)
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve instances list."))
        return instances

    def get_volumes_data(self):
        volumes = []
        try:
            volumes = api.resource_list(self.request, consts.CINDER_VOLUME)
            volumes = [os_api.cinder.Volume(v) for v in volumes]
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve volumes list."))
        return volumes

    def get_networks_data(self):
        nets = []
        try:
            nets = api.net_list_for_tenant(self.request,
                                           self.request.user.tenant_id)
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve network list."))
        return nets

    def get_security_groups_data(self):
        try:
            secgroups = api.sg_list(self.request, self.request.user.tenant_id)
        except Exception:
            secgroups = []
            exceptions.handle(self.request,
                              _('Unable to retrieve security groups.'))
        return sorted(secgroups, key=lambda group: group.name)

    def get_floating_ips_data(self):
        try:
            fips = api.resource_list(self.request, consts.NEUTRON_FLOATINGIP)
            LOG.info("a&s fips: %s", [ip.__dict__ for ip in fips])
        except Exception:
            fips = []
            exceptions.handle(self.request,
                              _('Unable to retrieve floating IP addresses.'))
        return fips

    def get_pools_data(self):
        pools = []
        try:
            request = self.request
            pools = api.resource_list(request, consts.NEUTRON_POOL)[0].pools
            pools = [os_api.lbaas.Pool(p) for p in pools]
        except Exception:
            exceptions.handle(self.request,
                              _('Unable to retrieve pools list.'))
        return pools
