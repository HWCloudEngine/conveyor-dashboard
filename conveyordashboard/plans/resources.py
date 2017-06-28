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

import base64
import json
import six
import uuid

from django.template import loader
from oslo_log import log as logging
from oslo_utils import strutils

from openstack_dashboard import api as os_api

from conveyordashboard.api import api
from conveyordashboard.common import constants as consts
from conveyordashboard.security_groups import tables as secgroup_tables

HAS_SERVER = 'HAS_SERVER'

LOG = logging.getLogger(__name__)


SHOW_KEY_MAP = {
    consts.NOVA_SERVER: {
        'OS-EXT-SRV-ATTR:user_data': 'user_data',
    },
    consts.NEUTRON_NET: {
        'router:external': 'router_external',
        'provider:physical_network': 'physical_network',
        'provider:segmentation_id': 'segmentation_id',
        'provider:network_type': 'network_type'
    }
}


class DetailResourceView(object):
    container = 'plans/res_detail/_balloon_container.html'

    def __init__(self, request, plan_id, res_type, res_id,
                 update_data):
        self.request = request
        self.plan_id = plan_id
        self.res_type = res_type
        self.res_id = res_id
        self.update_data = update_data

    def _trans_key(self, res):
        if self.res_type not in SHOW_KEY_MAP:
            return
        key_map = SHOW_KEY_MAP[self.res_type]
        for k, v in res.items():
            if k in key_map:
                res[key_map[k]] = v

    def _render_server(self, context):
        properties = context['data']
        if 'user_data' not in self.update_data:
            if properties.get('user_data', None):
                properties['user_data'] = \
                    base64.b64decode(properties['user_data']
                                     .encode('utf-8'))
        metadata = properties.get('metadata', {})
        if isinstance(metadata, dict):
            properties['metadata'] = '\n'.join(['%s=%s' % (k, v)
                                                for k, v in metadata.items()])
        return loader.render_to_string(self.container, context)

    def _render_keypair(self, context):
        properties = context['data']
        keypairs = api.resource_list(self.request, consts.NOVA_KEYPAIR)
        properties['keypairs'] = keypairs
        return loader.render_to_string(self.container, context)

    def _render_volume(self, context):
        properties = context['data']
        metadata = properties.get('metadata', {})
        if isinstance(metadata, dict):
            properties['metadata'] = '\n'.join(['%s=%s' % (k, v)
                                                for k, v in metadata.items()])

        if 'copy_data' not in properties:
            properties['copy_data'] = self.res.get('extra_properties',
                                                   {}).get('copy_data', True)

        return loader.render_to_string(self.container, context)

    def _render_volumetype(self, context):
        vts = api.resource_list(self.request, consts.CINDER_VOL_TYPE)
        context['data']['volumetypes'] = vts
        return loader.render_to_string(self.container, context)

    def _render_qos(self, context):
        properties = context['data']
        specs = '\n'.join(['%s=%s' % (k, v)
                           for k, v in properties.get('specs', {}).items()])
        properties['specs'] = specs
        return loader.render_to_string(self.container, context)

    def _render_net(self, context):
        properties = context['data']

        if properties.get(HAS_SERVER):
            is_external = properties['router_external']
            tenant_id = self.request.user.tenant_id
            networks = api.net_list_for_tenant(self.request, tenant_id)
            networks = [network for network in networks
                        if (getattr(network, 'router:external') == is_external
                            and len(network.subnets) > 0)]

            properties['networks'] = networks

        return loader.render_to_string(self.container, context)

    def _render_subnet(self, context):
        properties = context['data']
        properties['gateway_ip'] = properties['gateway_ip'] or ''
        if 'no_gateway' not in properties:
            properties['no_gateway'] = (properties['gateway_ip'] is None)
        if 'dns_nameservers' in properties \
                and isinstance(properties['dns_nameservers'], list):
            properties['dns_nameservers'] = \
                '\n'.join(properties['dns_nameservers'])
        if 'allocation_pools' in properties \
                and isinstance(properties['allocation_pools'], list):
            pools = ['%s,%s' % (p['start'], p['end'])
                     for p in properties['allocation_pools']]
            properties['allocation_pools'] = '\n'.join(pools)
        if 'host_routes' in properties \
                and isinstance(properties['host_routes'], list):
            routes = ['%s,%s' % (r['destination'], r['nexthop'])
                      for r in properties['host_routes']]
            properties['host_routes'] = '\n'.join(routes)

        if properties.get(HAS_SERVER):
            search_opts = {'network_id': properties.get('network_id')}
            subnets = api.subnet_list(self.request, search_opts=search_opts)
            properties['subnets'] = subnets

        return loader.render_to_string(self.container, context)

    def _render_port(self, context):
        fixed_ips = context['data']['fixed_ips']

        # Get detail subnet information for each fixed ip in fixed_ips.
        # And Unite the format for fixed_ips.
        for fixed_ip in fixed_ips:
            subnet_id = fixed_ip['subnet_id']

            subnet = api.resource_get(self.request,
                                      consts.NEUTRON_SUBNET,
                                      subnet_id)
            fixed_ip['cidr'] = subnet['cidr']
            fixed_ip['allocation_pools'] \
                = json.dumps(subnet['allocation_pools'])
        return loader.render_to_string(self.container, context)

    def _render_securitygroup(self, context):
        properties = context['data']
        rules = properties['security_group_rules']

        def rebuild_rules(r):
            def_r = {'remote_ip_prefix': None, 'remote_group_id': None,
                     'ethertype': None, 'security_group_id': None,
                     'direction': None, 'protocol': None,
                     'port_range_min': None, 'port_range_max': None}
            return dict(def_r, **r)

        if rules:
            if isinstance(rules, six.string_types):
                rules = json.JSONDecoder().decode(rules)
            else:
                for r in rules:
                    if 'id' not in r:
                        r['id'] = str(uuid.uuid4())
            tmp_rs = [os_api.neutron.SecurityGroupRule(rebuild_rules(r))
                      for r in rules]
            properties['rules'] = json.dumps(rules)
            rules_table = secgroup_tables.RulesTable(self.request, tmp_rs,
                                                     secgroup_id=context['id'])
            context['rules_table'] = rules_table.render()

        if properties.get(HAS_SERVER):
            tenant_id = self.request.user.tenant_id
            secgroups = api.sg_list(self.request, tenant_id)
            properties['secgroups'] = secgroups

        return loader.render_to_string(self.container, context)

    def _render_router(self, context):
        props = context['data']
        props['admin_state_up'] = strutils.bool_from_string(
            props['admin_state_up'])
        return loader.render_to_string(self.container, context)

    def render(self):
        resource = api.resource_get(self.request, self.res_type, self.res_id)
        self._trans_key(resource)

        LOG.info("Render id: %s\ntype: %s \nresource %s \nupdate_data %s",
                 self.res_id, self.res_type, resource, self.update_data)
        self.res = resource

        resource.update(self.update_data)

        node_type = self.res_type.split('::')[-1].lower()
        method = '_render_' + node_type
        template_name = ''.join(['plans/res_detail/', node_type, '.html'])

        context = {'type': node_type,
                   'template_name': template_name,
                   'resource_type': self.res_type,
                   'resource_id': self.res_id,
                   'id': self.res_id,
                   'data': resource}

        if hasattr(self, method):
            return getattr(self, method)(context)

        return loader.render_to_string(self.container, context)
