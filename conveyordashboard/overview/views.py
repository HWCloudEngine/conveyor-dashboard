# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

from django import http
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from horizon import exceptions
from horizon import views

from openstack_dashboard import api as os_api

from conveyordashboard.api import api
from conveyordashboard.common import constants as consts
from conveyordashboard.overview import tables as overview_tables 

from conveyordashboard.access_and_security.tables import FloatingIPsTable
from conveyordashboard.access_and_security.tables import SecurityGroupsTable
from conveyordashboard.instances.tables import InstancesTable
from conveyordashboard.loadbalancers.tables import PoolsTable
from conveyordashboard.networks.tables import NetworksTable
from conveyordashboard.volumes.tables import VolumesTable

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
    template_name = 'overview/index.html'

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
        context['table'] = overview_tables.ResTable(self.request, data=data).render()
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
        try:
            instances = api.resource_list(self.request, consts.NOVA_SERVER)
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve instances list."))
        return instances

    def get_volumes_data(self):
        try:
            volumes = api.resource_list(self.request, consts.CINDER_VOLUME)
            volumes = [os_api.cinder.Volume(v) for v in volumes]
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve volumes list."))
        return volumes

    def get_networks_data(self):
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


TYPE_CLASS_MAPPING = {
    consts.NOVA_SERVER: InstancesTable,
    consts.CINDER_VOLUME: VolumesTable,
    consts.NEUTRON_POOL: PoolsTable,
    consts.NEUTRON_NET: NetworksTable,
    consts.NEUTRON_FLOATINGIP: FloatingIPsTable,
    consts.NEUTRON_SECGROUP:SecurityGroupsTable
}


class RowActionsView(generic.View):
    @staticmethod
    def get(request, **kwargs):
        res_type = request.GET['res_type']
        id = request.GET['id']
        next_url = request.GET.get('next_url', None)
        res = api.ResourceDetail(request, res_type, id).get()
        if res_type in TYPE_CLASS_MAPPING:
            table = TYPE_CLASS_MAPPING[res_type](request, next_url=next_url)
            actions = table.render_row_actions(res)
            return http.HttpResponse(actions, content_type='text/html')


class TableActionsView(generic.View):
    @staticmethod
    def get(request, **kwargs):
        res_type = request.GET['res_type']
        if res_type in TYPE_CLASS_MAPPING:
            table = TYPE_CLASS_MAPPING[res_type](request)
            table_actions = table.render_table_actions()
            return http.HttpResponse(table_actions, content_type='text/html')
