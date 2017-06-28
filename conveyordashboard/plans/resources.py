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
import copy
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

DEPENDENCY_UPDATE_MAPPING = consts.DEPENDENCY_UPDATE_MAPPING
TAG_RES_TYPE = consts.TAG_RES_TYPE
TAG_RES_ID = consts.TAG_RES_ID
TAG_FROM = consts.TAG_FROM
TAG_FROM_ID = consts.TAG_FROM_ID
TAG_UPDATED = consts.TAG_UPDATED

ACTION_KEY = consts.RES_ACTION_KEY
ACTION_DELETE = consts.ACTION_DELETE
ACTION_ADD = consts.ACTION_ADD

LOG = logging.getLogger(__name__)


def rebuild_dependencies(dependencies):
    """Add reverse dependencies to original dependencies.

    :param dependencies: Original dependencies.
    """
    for res_id, item in dependencies.items():
        if item['dependencies']:
            for d in item['dependencies']:
                if d not in dependencies:
                    LOG.info('%s not in %s', d, dependencies)
                    continue
                if res_id not in dependencies[d]['dependencies']:
                    dependencies[d]['dependencies'].append(res_id)


def search_dependent_items(dependencies,
                           res_ids,
                           search_res_type,
                           excepts=None):
    """Search dependent item.

    :param dependencies:    dependencies used to search.
    :param res_ids:         list of resource id in heat template.
    :param search_res_type: destination resource type that needed to be search.
                            like: server
    :param excepts:         list of resource id. The search result should not
                            contain them.
    :return:                The list of id matched to search_res_type.
    """
    if not excepts:
        excepts = []

    searched_ids = []

    dep_pro = 'dependencies'
    for res_id in res_ids:
        if 'searched' in dependencies[res_id]:
            continue
        for dep_res_id in dependencies[res_id][dep_pro]:
            dependencies[res_id]['searched'] = True
            if search_res_type == dep_res_id.split("_")[0]:
                dependencies[res_id]['searched'] = True
                searched_ids.append(dep_res_id)
            else:
                searched_ids.extend(search_dependent_items(dependencies,
                                                           [dep_res_id],
                                                           search_res_type,
                                                           excepts=excepts))
    for e in excepts:
        if e in searched_ids:
            searched_ids.remove(e)

    return searched_ids


def is_in(arr, key, value):
    for res in arr:
        if getattr(res, key) == value:
            return True
    return False


class ResourceDetailFromPlan(object):
    container = 'plans/res_detail/_balloon_container.html'

    def __init__(self, request, plan_id, res_type, res_id,
                 update_data, updated_res=None, is_original=True):
        self.request = request
        self.plan_id = plan_id
        self.res_type = res_type
        self.res_id = res_id
        self.update_data = update_data
        if not updated_res:
            updated_res = {}
        self.updated_res = updated_res
        self.is_original = is_original

    def _render_server(self, context):
        props = context['data']
        if 'user_data' not in self.update_data:
            if props.get('user_data', None):
                props['user_data'] = \
                    base64.b64decode(props['user_data']
                                     .encode('utf-8'))
        metadata = props.get('metadata', {})
        if isinstance(metadata, dict):
            props['metadata'] = '\n'.join(['%s=%s' % (k, v)
                                           for k, v in metadata.items()])
        return loader.render_to_string(self.container, context)

    def _render_keypair(self, context):
        resource_detail = context['data']
        keypairs = api.resource_list(self.request, consts.NOVA_KEYPAIR)
        resource_detail['keypairs'] = keypairs
        return loader.render_to_string(self.container, context)

    def _render_volume(self, context):
        props = context['data']
        metadata = props.get('metadata', {})
        if isinstance(metadata, dict):
            props['metadata'] = '\n'.join(['%s=%s' % (k, v)
                                           for k, v in metadata.items()])

        if 'copy_data' not in props:
            props['copy_data'] = self.res.get('extra_properties',
                                              {}).get('copy_data', True)

        plan = api.plan_get(self.request, self.plan_id)
        dependencies = plan.updated_dependencies
        updated_res = dict(plan.updated_resources, **self.updated_res)
        rebuild_dependencies(dependencies)
        dep_servers = search_dependent_items(dependencies,
                                             [self.res_id],
                                             'server')

        if len(dep_servers):
            dep_volumes = search_dependent_items(copy.deepcopy(dependencies),
                                                 dep_servers,
                                                 'volume',
                                                 excepts=[self.res_id])
            volumes = api.resource_list(self.request, consts.CINDER_VOLUME)
            volumes = dict([(s.id, s) for s in volumes])
            for dep_volume in dep_volumes:
                if updated_res[dep_volume]['id'] in volumes:
                    del volumes[updated_res[dep_volume]['id']]
            vols = volumes.values()
            if not is_in(vols, 'id', context['id']):
                vols.insert(0, {'id': context['id'], 'name': ''})
            props['volumes'] = vols

        return loader.render_to_string(self.container, context)

    def _render_volumetype(self, context):
        vts = api.resource_list(self.request, consts.CINDER_VOL_TYPE)
        if not is_in(vts, 'id', context['id']):
            vts.append({'id': context['id'], 'name': ''})
        context['data']['volumetypes'] = vts
        return loader.render_to_string(self.container, context)

    def _render_qos(self, context):
        props = context['data']
        specs = '\n'.join(['%s=%s' % (k, v)
                           for k, v in props.get('specs', {}).items()])
        props['specs'] = specs
        return loader.render_to_string(self.container, context)

    def _render_net(self, context):
        props = context['data']
        val_specs = props.get('value_specs', {})
        if 'router_external' not in val_specs \
                and 'router:external' in val_specs:
            val_specs['router_external'] = val_specs['router:external']
        if 'segmentation_id' not in val_specs \
                and 'provider:segmentation_id' in val_specs:
            val_specs['segmentation_id'] \
                = val_specs['provider:segmentation_id']
        if 'physical_network' not in val_specs \
                and 'provider:physical_network' in val_specs:
            val_specs['physical_network'] \
                = val_specs['provider:physical_network']
        if 'network_type' not in val_specs \
                and 'provider:network_type' in val_specs:
            val_specs['network_type'] = val_specs['provider:network_type']
        props['admin_state_up'] \
            = strutils.bool_from_string(props['admin_state_up'])

        is_external = val_specs['router_external']
        tenant_id = self.request.user.tenant_id
        networks = api.net_list_for_tenant(self.request, tenant_id)
        networks = [network for network in networks
                    if (getattr(network, 'router:external') == is_external
                        and len(network.subnets) > 0)]

        # Remove conflict network
        plan = api.plan_get(self.request, self.plan_id)
        dependencies = plan.updated_dependencies
        updated_res = dict(plan.updated_resources, **self.updated_res)
        rebuild_dependencies(dependencies)
        dep_servers = search_dependent_items(copy.deepcopy(dependencies),
                                             [self.res_id],
                                             'server')
        if len(dep_servers):
            dep_networks = search_dependent_items(copy.deepcopy(dependencies),
                                                  dep_servers,
                                                  'network',
                                                  excepts=[self.res_id])

            networks = dict([(n.id, n) for n in networks])
            for dep_network in dep_networks:
                if updated_res[dep_network]['id'] in networks:
                    del networks[updated_res[dep_network]['id']]
            nets = networks.values()
            if not is_in(nets, 'id', context['id']):
                nets.insert(0, {'id': context['id'], 'name': ''})
            context['data']['networks'] = nets
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

        plan = api.plan_get(self.request, self.plan_id)
        dependencies = plan.updated_dependencies
        updated_res = dict(plan.updated_resources, **self.updated_res)

        search_opts = {}
        if 'from_network_id' in properties:
            search_opts['network_id'] = properties['from_network_id']
        else:
            net_name = properties.get('network_id')['get_resource']
            search_opts['network_id'] = updated_res.get(net_name, {}).get('id')
        subnets = api.subnet_list_for_tenant(self.request,
                                             self.request.user.tenant_id,
                                             search_opts=search_opts)

        # Remove conflict subnet.
        rebuild_dependencies(dependencies)
        dep_servers = search_dependent_items(copy.deepcopy(dependencies),
                                             [self.res_id],
                                             'server')
        if len(dep_servers):
            dep_subnets = search_dependent_items(copy.deepcopy(dependencies),
                                                 dep_servers,
                                                 'subnet',
                                                 excepts=[self.res_id])
            subnets = dict([(s.id, s) for s in subnets])
            for dep_subnet in dep_subnets:
                if updated_res[dep_subnet]['id'] in subnets:
                    del subnets[updated_res[dep_subnet]['id']]
            subnets = subnets.values()
            if not is_in(subnets, 'id', context['id']):
                subnets.insert(0, {'id': context['id'], 'name': ''})
            properties['subnets'] = subnets

        return loader.render_to_string(self.container, context)

    def _render_port(self, context):
        plan = api.plan_get(self.request, self.plan_id)
        fixed_ips = context['data']['fixed_ips']

        # Get detail subnet information for each fixed ip in fixed_ips.
        # And Unite the format for fixed_ips.
        for fixed_ip in fixed_ips:
            fip_subnet_id = fixed_ip['subnet_id']
            if isinstance(fip_subnet_id, str):
                subnet_id = fip_subnet_id
                for key, res in self.updated_res.items():
                    if res['id'] == subnet_id:
                        fixed_ip['subnet_id'] = {'get_resource': key}
                if not isinstance(fixed_ip['subnet_id'], dict):
                    for key, res in plan.updated_dependencies.items():
                        if res['id'] == subnet_id:
                            fixed_ip['subnet_id'] = {'get_resource': key}
            elif isinstance(fip_subnet_id, dict):
                if fip_subnet_id.get('get_resource', None):
                    res_id_subnet = fip_subnet_id['get_resource']
                elif fip_subnet_id.get('get_param', None):
                    subnet_id = self.res.get('parameters', {})\
                        .get(fip_subnet_id['get_param'], None)
                    if not subnet_id:
                        raise Exception
                    for key, res in self.updated_res.items():
                        if res['id'] == subnet_id:
                            fixed_ip['subnet_id'] = {'get_resource': key}
                    if 'get_resource' not in fixed_ip['subnet_id']:
                        for key, res in plan.updated_dependencies.items():
                            if res['id'] == subnet_id:
                                fixed_ip['subnet_id'] = {'get_resource': key}
                else:
                    raise Exception

                if res_id_subnet in self.updated_res:
                    subnet_id = self.updated_res[res_id_subnet]['id']
                else:
                    subnet_id = plan.updated_dependencies[res_id_subnet]['id']
            else:
                raise Exception
            subnet = api.resource_detail(self.request,
                                         consts.NEUTRON_SUBNET,
                                         subnet_id)
            fixed_ip['cidr'] = subnet['cidr']
            fixed_ip['allocation_pools'] \
                = json.dumps(subnet['allocation_pools'])
        return loader.render_to_string(self.container, context)

    def _render_securitygroup(self, context):
        props = context['data']
        rules = props['rules']

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
            props['rules'] = json.dumps(rules)
            rules_table = secgroup_tables.RulesTable(self.request, tmp_rs,
                                                     secgroup_id=context['id'])
            context['rules_table'] = rules_table.render()

        plan = api.plan_get(self.request, self.plan_id)
        dependencies = plan.updated_dependencies
        rebuild_dependencies(dependencies)
        dep_servers = search_dependent_items(dependencies,
                                             [self.res_id],
                                             'server')

        if len(dep_servers):
            tenant_id = self.request.user.tenant_id
            secgroups = api.sg_list(self.request, tenant_id)
            if not is_in(secgroups, 'id', context['id']):
                secgroups.insert(0, {'id': context['id'], 'name': ''})
            context['data']['secgroups'] = secgroups

        return loader.render_to_string(self.container, context)

    def _render_router(self, context):
        props = context['data']
        props['admin_state_up'] = strutils.bool_from_string(
            props['admin_state_up'])
        routers = api.resource_list(self.request, self.res_type)
        context['data']['routers'] = routers
        return loader.render_to_string(self.container, context)

    def _render_floatingip(self, context):
        plan = api.plan_get(self.request, self.plan_id)
        dependencies = plan.updated_dependencies
        rebuild_dependencies(dependencies)
        dep_servers = search_dependent_items(dependencies,
                                             [self.res_id],
                                             'server')
        # If current topology doesn't contain Server, then deny user to
        # select floating ip from existed items.
        if len(dep_servers):
            fip_id = plan.original_resources[self.res_id]['id']
            fips = api.resource_list(self.request, self.res_type)
            fips = [fip for fip in fips
                    if fip.status == 'DOWN' or fip.id == fip_id]
            if not is_in(fips, 'id', context['id']):
                fips.insert(0,
                            {'id': context['id'], 'floating_ip_address': ''})
            context['data']['fips'] = fips
        return loader.render_to_string(self.container, context)

    def render(self):
        if 'id' in self.update_data:
            resource = self.updated_res[self.res_id]
        else:
            # If the plan does not contain this resource, it will throw an
            # exception, then need to extract resource from api resource_get.
            resource = api.resource_detail_from_plan(self.request,
                                                     self.res_id,
                                                     self.plan_id,
                                                     self.is_original)
        LOG.info("Render id: %s\ntype: %s \nresource %s \nupdate_data %s",
                 self.res_id, self.res_type, resource, self.update_data)
        self.res = resource

        resource_detail = resource['properties']
        resource_detail.update(self.update_data)

        node_type = self.res_type.split('::')[-1].lower()
        method = '_render_' + node_type
        template_name = ''.join(['plans/res_detail/', node_type, '.html'])

        context = {'type': node_type,
                   'template_name': template_name,
                   'resource_type': self.res_type,
                   'resource_id': self.res_id,
                   'id': resource.get('id', ''),
                   'data': resource_detail}

        if hasattr(self, method):
            return getattr(self, method)(context)

        return loader.render_to_string(self.container, context)


def get_attr(obj, key, default=None):
    try:
        return obj.get(key, default)
    except (TypeError, KeyError):
            return getattr(obj, key, default)


def generate_template_name():
    return str(uuid.uuid4())[:12]


def build_volumetype(vt, template_name=None,
                     properties=None, dependencies=None):
    """Build OS::Cinder::VolumeType resource and dependency.

    :param qos: The volume_type dict or object.
    :param template_name: The name in template.
    :param properties: The extra properties.
                       This will cover the existed in volume_type
    :param dependencies: The extra deps.
                         This will cover the existed in volume_type
    :return: volume_type resource and dependency
    """
    if not template_name:
        template_name = generate_template_name()

    vt_id = get_attr(vt, 'id')
    name = get_attr(vt, 'name')
    res = {
        'id': vt_id,
        'type': consts.CINDER_VOL_TYPE,
        'name': template_name,
        'properties': {
            'name': get_attr(vt, 'name')
        },
        'extra_properties': {
            'id': vt_id
        },
        'parameters': {}
    }
    extra_specs = get_attr(vt, 'extra_specs')
    if extra_specs:
        res['properties']['metadata'] = extra_specs
    if properties is not None and isinstance(properties, dict):
        res['properties'].update(properties)

    dep = {
        'name_in_template': template_name,
        'dependencies': [],
        'type': consts.CINDER_VOL_TYPE,
        'id': vt_id,
        'name': name
    }
    if dependencies is not None and isinstance(dependencies, list):
        dep['dependencies'].extend(dependencies)
    return res, dep


def build_qos(qos, template_name=None, properties=None, dependencies=None):
    """Build OS::Cinder::Qos resource and dependency.

    :param qos: The Qos dict or object.
    :param template_name: The name in template.
    :param properties: The extra properties. This will cover the existed in qos
    :param dependencies: The extra deps. This will cover the existed in qos
    :return: Qos resource and dependency
    """
    if not template_name:
        template_name = generate_template_name()

    qos_id = get_attr(qos, 'id')
    name = get_attr(qos, 'name')

    res = {
        'id': qos_id,
        'type': consts.CINDER_QOS,
        'name': template_name,
        'properties': {
            'name': get_attr(qos, 'name'),
            'specs': get_attr(qos, 'specs', {})
        },
        'extra_properties': {
            'id': qos_id
        }
    }
    if properties is not None and isinstance(properties, dict):
        res['properties'].update(properties)

    dep = {
        'name_in_template': template_name,
        'dependencies': [],
        'type': consts.CINDER_QOS,
        'id': qos_id,
        'name': name
    }
    if dependencies is not None and isinstance(dependencies, list):
        dep['dependencies'].extend(dependencies)
    return res, dep


class PlanUpdate(object):
    """Update plan"""
    def __init__(self, request, plan_id, updated_resources, dependencies,
                 update_resource=None):
        """Update the resources of plan.

        :param request:
        :param plan_id:
        :param updated_resources:   the full detail of resources that
                                    have been updated.
        :type updated_resources: dict
        :param dependencies:        the dependencies that have been updated.
        :type dependencies: list
        :param update_resource:     the collection of updated items of this
                                    resource.
        :type update_resource: dict
        """

        self.request = request
        self.plan_id = plan_id
        self.updated_resources = updated_resources
        self.dependencies = dependencies
        if not update_resource:
            update_resource = {}
        self.update_resource = update_resource

    def _dependent_items(self, res_id=None, res_type=None,
                         dep_type=None, excepts=None):
        if not res_id:
            res_id = self.res_id
        if not res_type:
            res_type = self.res_type
        if not dep_type:
            dependent_type = DEPENDENCY_UPDATE_MAPPING.get(res_type, [])
        elif isinstance(dep_type, six.string_types):
            dependent_type = [dep_type]
        else:
            dependent_type = dep_type
        if excepts is None:
            excepts = []
        LOG.info("Get dependent items.\nresource_type=%(res_type)s\n"
                 "resource_id=%(res_id)s\ndep_type=%(dep_type)s\n"
                 "excepts=%(excepts)s",
                 {'res_type': res_type, 'res_id': res_id,
                  'dep_type': dependent_type, 'excepts': excepts})

        dependent_items = {}

        if res_id not in self.dependencies:
            return dependent_items

        this_res = self.dependencies[res_id]

        for key, value in self.dependencies.items():
            if value['type'] in dependent_type \
                    and (res_id in value['dependencies']
                         or key in this_res['dependencies']) \
                    and key not in excepts:
                dependent_items[key] = value
        LOG.info("Get dependent items.%s\n", dependent_items)
        return dependent_items

    def execute(self, data):
        LOG.info("Update Plan {0} with data {1}".format(self.plan_id, data))
        self.res_type = data.pop(TAG_RES_TYPE)
        self.res_id = data.pop(TAG_RES_ID)
        self.data = data
        method = '_update_' + self.res_type.split('::')[-1].lower()
        if hasattr(self, method):
            getattr(self, method)()

    def execute_return(self):
        return self.updated_resources, self.dependencies, self.update_resource

    def update_updated_resources(self, param):
        self.updated_resources[self.res_id].update(param)

    def update_dependencies(self, param):
        self.dependencies[self.res_id].update(param)

    def update_update_resource(self, param):
        param[TAG_RES_TYPE] = self.res_type
        param[TAG_RES_ID] = self.res_id
        self.update_resource.update({self.res_id: param})

    def _get_depended_items(self, res_id):
        items = {}
        for k, v in self.dependencies.items():
            if res_id in v['dependencies']:
                items[k] = v
        return items

    def _check_existed_from_deps(self, os_res_id):
        """Check the given OpenStack resource uuid already exists in
        dependencies.
        :param os_res_id: The OpenStack resource uuid.
        :return: (False, None) or (True, existed_item)
        :rtype: tuple
        """
        item = None
        for k, v in self.dependencies.items():
            if v['id'] == os_res_id:
                item = v
        return True if item is not None else False, item

    def _remove_delete_flag(self, res_id):
        if self.dependencies[res_id].get(ACTION_KEY, None) == ACTION_DELETE:
            LOG.debug("Remove action 'delete' flag for %s", res_id)
            self.dependencies[res_id].pop(ACTION_KEY)
            self.updated_resources[res_id].pop(ACTION_KEY)
            self.update_resource[res_id].pop(ACTION_KEY, None)

    def _update_keypair(self):
        LOG.info("Update key pair")
        data = self.data
        res_id = self.res_id
        res_type = self.res_type
        this_res = self.updated_resources[res_id]
        keypair_name = self.data.get('name', None)
        if not keypair_name:
            return

        action_type = data.get('action_type', 'update')
        keypairs = api.resource_list(self.request, res_type)
        if action_type == 'update':
            keypair_name = data.get('name', None)
            if not keypair_name:
                return

            keypair = None
            for item in keypairs:
                if item.name == keypair_name:
                    keypair = item
                    break
            if not keypair:
                return

            new_id = keypair_name
            this_res.update({
                'id': new_id,
                TAG_UPDATED: True,
                'properties': {
                    'public_key': keypair.public_key,
                    'name': keypair_name}})
            self.dependencies.get(res_id).update({'id': new_id,
                                                  'name': keypair_name})
            self.update_resource.update({
                res_id: {TAG_RES_TYPE: res_type,
                         TAG_RES_ID: res_id,
                         'name': keypair_name,
                         'public_key': keypair.public_key,
                         'id': new_id}})

    def _update_volume_with_vt(self, new_vol, dep_items):
        LOG.info("Update volume with volume type.")
        if len(dep_items) == 0:
            return

        data = self.data
        vol_id = data['id']
        res_id = self.res_id
        if not new_vol['volume_type']:
            for key, value in dep_items.items():
                self.dependencies[res_id]['dependencies'].remove(key)
                if len([k for k, v in self.dependencies.items()
                        if k != res_id and key in v['dependencies']]) == 0:
                    data = {
                        TAG_RES_TYPE: value['type'],
                        TAG_RES_ID: key,
                        TAG_FROM: 'volume',
                        TAG_FROM_ID: res_id,
                        'volume_id': vol_id,
                        ACTION_KEY: ACTION_DELETE
                    }
                    self.execute(data)
        else:
            vts = api.resource_list(self.request, consts.CINDER_VOL_TYPE)
            new_vt = None
            for vt in vts:
                if vt.name == new_vol['volume_type']:
                    new_vt = vt
                    break
            if new_vt is None:
                return

            for key, value in dep_items.items():
                # These two volume type are the same one.
                if new_vt.id == value['id']:
                    continue

                # The new vt exists in plan.
                item = None
                for k, v in self.dependencies.items():
                    if v['id'] == new_vt.id:
                        item = v
                if item is not None:
                    self.dependencies[res_id]['dependencies'].remove(key)
                    vt_tmpl_name = item['name_in_template']
                    self.dependencies[res_id]['dependencies']\
                        .append(vt_tmpl_name)

                    # Remove ACTION 'delete' flag for volum volume type.
                    if self.dependencies[vt_tmpl_name]\
                            .get(ACTION_KEY, '') == ACTION_DELETE:
                        LOG.debug(
                            "Remove action 'delete' flag for volume_type: %s",
                            vt_tmpl_name)
                        self.dependencies[vt_tmpl_name].pop(ACTION_KEY, None)
                        self.updated_resources[vt_tmpl_name].pop(ACTION_KEY)
                        self.update_resource[vt_tmpl_name].pop(ACTION_KEY,
                                                               None)
                        vt_deps = self._dependent_items(
                            res_id=vt_tmpl_name,
                            res_type=consts.CINDER_VOL_TYPE,
                            dep_type=[consts.CINDER_QOS]
                        )
                        if len(vt_deps):
                            for qos_id in vt_deps.keys():
                                if self.dependencies[qos_id]\
                                        .get(ACTION_KEY,
                                             None) == ACTION_DELETE:
                                    LOG.debug(
                                        "Remove action 'delete' "
                                        "flag for qos: %s",
                                        qos_id)
                                    self.dependencies[qos_id].pop(ACTION_KEY)
                                    self.updated_resources[qos_id].pop(
                                        ACTION_KEY)
                                    self.update_resource[qos_id].pop(
                                        ACTION_KEY)

                    if not len([k1 for k1, v1 in self.dependencies.items()
                                if key in v1['dependencies']]):
                        data = {
                            ACTION_KEY: ACTION_DELETE,
                            TAG_RES_TYPE: value['type'],
                            TAG_RES_ID: key,
                            TAG_FROM: 'volume',
                            TAG_FROM_ID: res_id,
                            'volume_id': vol_id
                        }
                        self.execute(data)
                # The new vt does not exist in plan.
                else:
                    self.dependencies[res_id]['dependencies'].remove(key)
                    new_qos_id = new_vt.qos_specs_id
                    vt_deps = []
                    vt_props = {}
                    if new_qos_id:
                        qos_dep = None
                        for v in self.dependencies.values():
                            if v['id'] == new_qos_id:
                                qos_dep = v
                        if qos_dep is not None:
                            qos_tmpl_name = qos_dep['name_in_template']
                            vt_deps.append(qos_tmpl_name)
                            self._remove_delete_flag(qos_tmpl_name)
                        else:
                            new_qos = api.resource_detail(self.request,
                                                          consts.CINDER_QOS,
                                                          new_qos_id)

                            qos_res, qos_dep = build_qos(new_qos)
                            qos_tmpl_name = qos_res['name']
                            vt_deps.append(qos_tmpl_name)

                            qos_res.update({ACTION_KEY: ACTION_ADD})
                            self.updated_resources[qos_tmpl_name] = qos_res
                            qos_dep.update({ACTION_KEY: ACTION_ADD})
                            self.dependencies[qos_tmpl_name] = qos_dep

                            update_data = {
                                ACTION_KEY: ACTION_ADD,
                                TAG_RES_TYPE: consts.CINDER_QOS,
                                TAG_RES_ID: qos_tmpl_name,
                                'id': new_qos_id,
                                'properties': qos_res['properties']
                            }
                            self.update_resource[qos_tmpl_name] = update_data

                    # Add new volume type.
                    vt_res, vt_dep = build_volumetype(new_vt, props=vt_props,
                                                      deps=vt_deps)
                    vt_tmp_name = vt_dep['name_in_template']

                    # Add dependencies for volume.
                    self.dependencies[res_id]['dependencies'].append(
                        vt_tmp_name)

                    vt_res.update({ACTION_KEY: ACTION_ADD})
                    self.updated_resources[vt_tmp_name] = vt_res
                    vt_dep.update({ACTION_KEY: ACTION_ADD})
                    self.dependencies[vt_tmp_name] = vt_dep
                    update_data = {
                        ACTION_KEY: ACTION_ADD,
                        TAG_RES_TYPE: consts.CINDER_VOL_TYPE,
                        TAG_RES_ID: vt_tmp_name,
                        'id': new_vt.id,
                        'properties': vt_res['properties']
                    }
                    self.update_resource[vt_tmp_name] = update_data

                    if not len([k1 for k1, v1 in self.dependencies.items() if
                                key in v1['dependencies']]):
                        data = {
                            ACTION_KEY: ACTION_DELETE,
                            TAG_RES_TYPE: value['type'],
                            TAG_RES_ID: key,
                            TAG_FROM: 'volume',
                            TAG_FROM_ID: res_id,
                            'volume_id': vol_id
                        }
                        self.execute(data)

    def _update_volume_without_vt(self, new_vol):
        LOG.info("Update volume without volume type.")
        res_id = self.res_id
        if new_vol['volume_type']:
            vts = api.resource_list(self.request, consts.CINDER_VOL_TYPE)
            new_vt = None
            for vt in vts:
                if vt.name == new_vol['volume_type']:
                    new_vt = vt
                    break
            # TODO(drngsl) If there is not any matched volume_type, return.
            # Here not raise exception.
            if new_vt is None:
                return

            vt_id = new_vt.id
            existed, vt_dep = self._check_existed_from_deps(vt_id)
            if existed:
                # Add dependencies for Volume.
                vt_tmpl_name = vt_dep['name_in_template']
                self.dependencies[res_id]['dependencies'].append(vt_tmpl_name)

                # Remove ACTION 'delete' flag for volum volume type.
                if self.dependencies[vt_tmpl_name]\
                        .get(ACTION_KEY, '') == ACTION_DELETE:
                    LOG.debug("Remove action 'delete' flag for "
                              "volume_type: %s", vt_tmpl_name)
                    self.dependencies[vt_tmpl_name].pop(ACTION_KEY, None)
                    self.updated_resources[vt_tmpl_name].pop(ACTION_KEY)
                    self.update_resource[vt_tmpl_name].pop(ACTION_KEY, None)
                    vt_deps = self._dependent_items(
                        res_id=vt_tmpl_name,
                        res_type=consts.CINDER_VOL_TYPE,
                        dep_type=[consts.CINDER_QOS]
                    )
                    if len(vt_deps):
                        for qos_id in vt_deps.keys():
                            if self.dependencies[qos_id]\
                                    .get(ACTION_KEY, None) == ACTION_DELETE:
                                LOG.debug("Remove action 'delete' "
                                          "flag for qos: %s", qos_id)
                                self.dependencies[qos_id].pop(ACTION_KEY)
                                self.updated_resources[qos_id].pop(ACTION_KEY)
                                self.update_resource[qos_id].pop(ACTION_KEY)
            else:
                # Check qos.
                new_qos_id = new_vt.qos_specs_id
                vt_deps = []
                vt_props = {}
                if new_qos_id:
                    existed, qos_dep \
                        = self._check_existed_from_deps(new_qos_id)
                    if existed:
                        qos_tmp_name = qos_dep['name_in_template']
                        vt_deps.append(qos_tmp_name)
                        vt_props['qos_specs_id'] = {
                            'get_resource': qos_tmp_name
                        }
                        # Delete ACTION 'delete' flag for qos if needed.
                        self._remove_delete_flag(qos_tmp_name)
                    else:
                        new_qos = api.resource_detail(self.request,
                                                      consts.CINDER_QOS,
                                                      new_qos_id)
                        qos_res, qos_dep = build_qos(new_qos)

                        qos_tmp_name = qos_dep['name_in_template']
                        vt_deps.append(qos_tmp_name)

                        qos_res.update({ACTION_KEY: ACTION_ADD})
                        self.updated_resources[qos_tmp_name] = qos_res
                        qos_dep.update({ACTION_KEY: ACTION_ADD})
                        self.dependencies[qos_tmp_name] = qos_dep
                        update_data = {
                            ACTION_KEY: ACTION_ADD,
                            TAG_RES_TYPE: consts.CINDER_QOS,
                            TAG_RES_ID: qos_tmp_name,
                            'id': new_qos_id,
                            'properties': qos_res['properties']
                        }
                        self.update_resource[qos_tmp_name] = update_data

                # Add new volume type.
                vt_res, vt_dep = build_volumetype(new_vt,
                                                  properties=vt_props,
                                                  dependencies=vt_deps)
                vt_tmpl_name = vt_dep['name_in_template']
                vt_res.update({ACTION_KEY: ACTION_ADD})
                self.updated_resources[vt_tmpl_name] = vt_res
                vt_dep.update({ACTION_KEY: ACTION_ADD})
                self.dependencies[vt_tmpl_name] = vt_dep
                update_data = {
                    ACTION_KEY: ACTION_ADD,
                    TAG_RES_TYPE: consts.CINDER_VOL_TYPE,
                    TAG_RES_ID: vt_tmpl_name,
                    'id': new_vt.id,
                    'properties': vt_props
                }
                self.update_resource[vt_tmpl_name] = update_data

                # Add dependencies for volume.
                self.dependencies[res_id]['dependencies'].append(vt_tmpl_name)

    def _update_volume(self):
        LOG.info("Update volume.")
        data = self.data
        res_id = self.res_id
        res_type = self.res_type
        this_res = self.updated_resources[res_id]
        if this_res.get(TAG_UPDATED, False):
            return

        vol_id = data['id']
        new_vol = api.resource_detail(self.request, res_type, vol_id)
        LOG.info("new_vol: %s", new_vol)
        update_data = {
            'id': vol_id,
            TAG_UPDATED: True,
            'properties': {
                'name': new_vol['display_name'],
                'size': new_vol['size'],
                # 'description': new_vol['display_description'],
                'metadata': new_vol['volume_metadata']
            }
        }
        this_res.update(update_data)
        self.dependencies.get(res_id).update({
            'id': vol_id,
            'name': new_vol['display_name']
        })
        update_data = {
            res_id: dict({
                TAG_RES_TYPE: res_type,
                TAG_RES_ID: res_id,
                'id': vol_id
            }, **(this_res['properties']))
        }
        self.update_resource.update(update_data)
        # Check dependencies
        dependent_items = self._dependent_items(
            dep_type=consts.CINDER_VOL_TYPE)
        if len(dependent_items):
            return self._update_volume_with_vt(new_vol, dependent_items)
        else:
            return self._update_volume_without_vt(new_vol)

    def _update_volumetype_from_volume(self):
        LOG.info("Update volume type from volume")
        res_id = self.res_id
        res_type = self.res_type
        this_res = self.updated_resources[res_id]
        volume_id = self.data['volume_id']
        vol = api.resource_detail(self.request,
                                  consts.CINDER_VOLUME,
                                  volume_id)

        action = self.data.get(ACTION_KEY, None)
        if not action and action not in consts.RES_ACTIONS:
            return
        elif action == ACTION_DELETE:
            dependent_items = self._dependent_items()
            for key, value in dependent_items.items():
                data = {
                    TAG_RES_TYPE: value['type'],
                    TAG_RES_ID: key,
                    TAG_FROM: 'volumetype',
                    TAG_FROM_ID: res_id,
                    ACTION_KEY: ACTION_DELETE
                }
                self.execute(data)
            # Set the flag 'delete'.
            self.dependencies[res_id][ACTION_KEY] = ACTION_DELETE
            self.updated_resources[res_id][ACTION_KEY] = ACTION_DELETE
            if res_id in self.update_resource:
                self.update_resource[res_id][ACTION_KEY] = ACTION_DELETE
            else:
                update_data = {
                    ACTION_KEY: ACTION_DELETE,
                    TAG_RES_TYPE: res_type,
                    TAG_RES_ID: res_id,
                    'id': this_res['id'],
                    'properties': this_res['properties']
                }
                self.update_resource.update({res_id: update_data})
            return

        # If selected volume type does not associate
        # with some qos, then return.
        if not vol['volume_type']:
            return

        vts = api.resource_list(self.request, consts.CINDER_VOL_TYPE)
        new_vt = None
        for vt in vts:
            if vt.name == vol['volume_type']:
                new_vt = vt
                break
        update_data = {
            'id': new_vt.id,
            TAG_UPDATED: True,
            'properties': {'name': new_vt.name}
        }
        this_res.update(update_data)
        self.dependencies[res_id].update({'id': new_vt.id,
                                          'name': new_vt.name})
        update_data = {res_id: dict({TAG_RES_TYPE: res_type,
                                     TAG_RES_ID: res_id,
                                     'id': new_vt.id,
                                     'from_volume_id': volume_id},
                                    **(this_res['properties']))}
        self.update_resource.update(update_data)
        pass

    def _update_volumetype_with_qos(self, vt, dep_items):
        LOG.info("Update volume type with qos.")
        data = self.data
        vt_id = data['id']
        res_id = self.res_id
        qos_id = vt['qos_specs_id']
        if not qos_id:
            for key, value in dep_items.items():
                self.dependencies[res_id]['dependencies'].remove(key)
                if len([k for k, v in self.dependencies.items() if
                        k != res_id and key in v['dependencies']]) == 0:
                    data = {
                        ACTION_KEY: ACTION_DELETE,
                        TAG_RES_TYPE: value['type'],
                        TAG_RES_ID: key,
                        TAG_FROM: 'volumetype',
                        TAG_FROM_ID: res_id,
                        'volume_type_id': vt_id
                    }
                    self.execute(data)
        else:
            new_qos = api.resource_detail(self.request,
                                          consts.CINDER_QOS,
                                          qos_id)

            for key, value in dep_items.items():
                # These two volume type are the same one.
                if new_qos['id'] == value['id']:
                    continue

                # The new qos exists in plan.
                item = None
                for k, v in self.dependencies.items():
                    if v['id'] == new_qos['id']:
                        item = v

                if item is not None:
                    # Remove ACTION delete flag if needed.
                    self.dependencies[res_id]['dependencies'].remove(key)
                    tmpl_name = item['name_in_template']
                    self.dependencies[res_id]['dependencies'].append(tmpl_name)
                    if self.dependencies[tmpl_name]\
                            .get(ACTION_KEY, '') == ACTION_DELETE:
                        self.dependencies[tmpl_name].pop(ACTION_KEY)
                        self.updated_resources[tmpl_name].pop(ACTION_KEY)

                    # No other res dependent on old qos, the delete it.
                    if not len([k1 for k1, v1 in self.dependencies.items() if
                                key in v1['dependencies']]):
                        data = {
                            ACTION_KEY: ACTION_DELETE,
                            TAG_RES_TYPE: value['type'],
                            TAG_RES_ID: key,
                            TAG_FROM: 'volumetype',
                            TAG_FROM_ID: res_id,
                            'volumetype_id': vt_id
                        }
                        self.execute(data)
                # The new qos does not exist in plan.
                else:
                    qos_res, qos_dep = build_qos(new_qos)
                    qos_tmp_name = qos_res['name']

                    qos_res.update({ACTION_KEY: ACTION_ADD})
                    self.updated_resources[qos_tmp_name] = qos_res

                    self.dependencies[qos_tmp_name] = qos_dep

                    update_data = {
                        ACTION_KEY: ACTION_ADD,
                        TAG_RES_TYPE: consts.CINDER_QOS,
                        TAG_RES_ID: qos_tmp_name,
                        'id': qos_id,
                        'properties': qos_res['properties']
                    }
                    self.update_resource[qos_tmp_name] = update_data

                    # Add dependencies for volume.
                    self.dependencies[res_id]['dependencies'].remove(key)
                    self.dependencies[res_id]\
                        .get('dependencies', {})\
                        .append(qos_tmp_name)

                    # No other res dependent on old qos, the delete it.
                    if not len([k1 for k1, v1 in self.dependencies.items() if
                                key in v1['dependencies']]):
                        data = {
                            ACTION_KEY: ACTION_DELETE,
                            TAG_RES_TYPE: value['type'],
                            TAG_RES_ID: key,
                            TAG_FROM: 'volumetype',
                            TAG_FROM_ID: res_id,
                            'volumetype_id': vt_id
                        }
                        self.execute(data)

    def _update_volumetype_without_qos(self, vt):
        LOG.info("Update volume type without qos.")
        res_id = self.res_id
        qos_id = vt['qos_specs_id']
        if qos_id:
            existed, qos_dep = self._check_existed_from_deps(qos_id)
            if existed:
                # Add dependencies for volume type.
                qos_tmpl_name = qos_dep['name_in_template']
                self.dependencies[res_id]['dependencies'].append(qos_tmpl_name)
                if self.dependencies[qos_tmpl_name].get(ACTION_KEY,
                                                        '') == ACTION_DELETE:
                    self.updated_resources[qos_tmpl_name].pop(ACTION_KEY)
                    self.update_resource[qos_tmpl_name].pop(ACTION_KEY)
                    self.dependencies[qos_tmpl_name].pop(ACTION_KEY)
            else:
                new_qos = api.resource_detail(self.request,
                                              consts.CINDER_QOS,
                                              qos_id)
                qos_res, qos_dep = build_qos(new_qos)

                qos_tmp_name = qos_dep['name_in_template']
                qos_res.update({ACTION_KEY: ACTION_ADD})
                self.updated_resources[qos_tmp_name] = qos_res
                self.dependencies[qos_tmp_name] = qos_dep
                update_data = {
                    ACTION_KEY: ACTION_ADD,
                    TAG_RES_TYPE: consts.CINDER_QOS,
                    TAG_RES_ID: qos_tmp_name,
                    'id': qos_id,
                    'properties': qos_res['properties']
                }
                self.update_resource[qos_tmp_name] = update_data

                # Add new volume type.
                self.dependencies[res_id]['dependencies'].append(qos_tmp_name)
        pass

    def _update_volumetype(self):
        LOG.info("Update volume type.")
        data = self.data
        res_id = self.res_id
        res_type = self.res_type
        this_res = self.updated_resources[res_id]
        if this_res.get(TAG_UPDATED, False):
            return

        update_from = data.get(TAG_FROM, None)
        if update_from:
            if update_from == 'volume':
                self._update_volumetype_from_volume()
            return

        vt_id = data['id']
        # Check selected vt existing in plan.
        existed, item = self._check_existed_from_deps(vt_id)
        if existed:
            # Update volume.
            new_vt_tmpl_name = item['name_in_template']
            LOG.debug("Update dependent volumes for volume_type: %s",
                      new_vt_tmpl_name)
            dep_vols = self._dependent_items(dep_type=[consts.CINDER_VOLUME])
            if len(dep_vols):
                LOG.info("Get dependent volumes %s", dep_vols)
                for dep_vol_id, dep_vol in dep_vols.items():
                    self.dependencies[dep_vol_id]['dependencies']\
                        .remove(res_id)
                    self.dependencies[dep_vol_id]['dependencies']\
                        .append(new_vt_tmpl_name)
                    t_dep = {'volume_type': {'get_resource': new_vt_tmpl_name}}
                    self.updated_resources[dep_vol_id]\
                        .update({TAG_UPDATED: True})
                    if dep_vol_id in self.update_resource:
                        self.update_resource[dep_vol_id].get('properties', {})\
                            .update(t_dep)
                    else:
                        update_data = copy.deepcopy(
                            self.updated_resources[dep_vol_id])
                        update_data.update({
                            TAG_RES_TYPE: consts.CINDER_VOLUME,
                            TAG_RES_ID: dep_vol_id})
                        self.update_resource.update({dep_vol_id: update_data})
                    pass
            # Delete sign of ACTION_KEY if existed.
            if self.dependencies[new_vt_tmpl_name]\
                    .get(ACTION_KEY, '') == ACTION_DELETE:
                LOG.debug("Remove action 'delete' flag for volume_type: %s",
                          new_vt_tmpl_name)
                self.updated_resources[new_vt_tmpl_name].pop(ACTION_KEY)
                self.update_resource[new_vt_tmpl_name].pop(ACTION_KEY)
                self.dependencies[new_vt_tmpl_name].pop(ACTION_KEY)

                dep_qoses = self._dependent_items(
                    res_id=new_vt_tmpl_name,
                    res_type=consts.CINDER_VOL_TYPE,
                    dep_type=[consts.CINDER_QOS])
                if len(dep_qoses):
                    for qos_id in dep_qoses.keys():
                        if self.dependencies[qos_id]\
                                .get(ACTION_KEY, None) == ACTION_DELETE:
                            LOG.debug("Remove action 'delete' "
                                      "flag for qos: %s", qos_id)
                            self.dependencies[qos_id].pop(ACTION_KEY, None)
                            self.updated_resources[qos_id].pop(ACTION_KEY,
                                                               None)
                            # if qos_id in self.update_resource:
                            self.update_resource[qos_id].pop(ACTION_KEY, None)

            # Delete old vt and dependent qos.
            self.dependencies[res_id][ACTION_KEY] = ACTION_DELETE
            update_data = {
                TAG_RES_TYPE: res_type,
                TAG_RES_ID: res_id,
                'id': this_res['id'],
                ACTION_KEY: ACTION_DELETE
            }
            self.update_resource.update({res_id: update_data})
            self.updated_resources[res_id].update({ACTION_KEY: ACTION_DELETE})
            dep_qoses = self._dependent_items(dep_type=[consts.CINDER_QOS])
            for key, value in dep_qoses.items():
                data = {
                    ACTION_KEY: ACTION_DELETE,
                    TAG_RES_TYPE: value['type'],
                    TAG_RES_ID: key,
                    TAG_FROM: 'volumetype',
                    TAG_FROM_ID: res_id,
                    'volume_type_id': vt_id
                }
                self.execute(data)
            pass
        else:
            new_vt = api.resource_detail(self.request, res_type, vt_id)
            update_data = {'id': vt_id,
                           TAG_UPDATED: True,
                           'properties': {'name': new_vt['name']}}
            this_res.update(update_data)
            self.dependencies.get(res_id).update({'id': vt_id,
                                                  'name': new_vt['name']})
            update_data = {res_id: dict({TAG_RES_TYPE: res_type,
                                         TAG_RES_ID: res_id,
                                         'id': vt_id},
                                        **(this_res['properties']))}
            self.update_resource.update(update_data)

            # Update dependent items.
            dependent_items = self._dependent_items()
            if len(dependent_items):
                return self._update_volumetype_with_qos(new_vt,
                                                        dependent_items)
            else:
                return self._update_volumetype_without_qos(new_vt)

    def _update_qos_from_volume_type(self):
        LOG.info("Update qos from volume type.")
        res_id = self.res_id
        res_type = self.res_type
        this_res = self.updated_resources[res_id]

        LOG.info("data: %s", self.data)
        action = self.data.get(ACTION_KEY, None)
        if action == ACTION_DELETE:
            LOG.info("delete qos %s %s", res_id, self.update_resource)
            # Set the flag 'delete'
            self.dependencies[res_id][ACTION_KEY] = ACTION_DELETE
            self.updated_resources[res_id].update({ACTION_KEY: ACTION_DELETE})
            if res_id in self.update_resource:
                self.update_resource[res_id][ACTION_KEY] = ACTION_DELETE
            else:
                update_data = {
                    res_id: {
                        ACTION_KEY: ACTION_DELETE,
                        TAG_RES_TYPE: res_type,
                        TAG_RES_ID: res_id,
                        'id': this_res['id'],
                        'properties': this_res['properties']
                    }
                }
                self.update_resource.update(update_data)
            return

        volume_type_id = self.data['volume_type_id']
        vt = api.resource_detail(self.request,
                                 consts.CINDER_VOL_TYPE,
                                 volume_type_id)
        # If selected volume type does not associate
        # with some qos, then return.
        if not vt['qos_specs_id']:
            return

        qos = api.resource_detail(self.request,
                                  consts.CINDER_QOS,
                                  vt['qos_specs_id'])
        update_data = {'id': qos['id'],
                       TAG_UPDATED: True,
                       'properties': {'name': qos['name'],
                                      'specs': qos.get('specs', {})}}
        this_res.update(update_data)
        self.dependencies[res_id].update({'id': qos['id'],
                                          'name': qos['name']})
        update_data = {res_id: dict({TAG_RES_TYPE: res_type,
                                     TAG_RES_ID: res_id,
                                     'id': qos['id'],
                                     'from_volume_type_id': volume_type_id},
                                    **(this_res['properties']))}
        self.update_resource.update(update_data)

    def _update_qos(self):
        LOG.info("Update qos.")

        this_res = self.updated_resources[self.res_id]
        if this_res.get(TAG_UPDATED, None):
            return

        data = self.data
        update_from = data.get(TAG_FROM, None)
        if update_from:
            if update_from == 'volumetype':
                self._update_qos_from_volume_type()
        else:
            res_id = self.res_id
            res_type = self.res_type
            qos_id = data['id']
            new_qos = api.resource_detail(self.request, res_type, qos_id)
            update_data = {'id': qos_id,
                           TAG_UPDATED: True,
                           'properties': {'name': new_qos['name'],
                                          'specs': new_qos['specs']}}
            this_res.update(update_data)
            self.dependencies[res_id].update({'id': qos_id,
                                              'name': new_qos['name']})
            update_data = {res_id: dict({TAG_RES_TYPE: res_type,
                                         TAG_RES_ID: res_id,
                                         'id': qos_id},
                                        **(this_res['properties']))}
            self.update_resource.update(update_data)

    def _update_port(self):
        LOG.info("Update port")
        data = self.data
        res_id = self.res_id
        res_type = self.res_type
        this_res = self.updated_resources[res_id]

        update_from = data.get(TAG_FROM, None)
        if update_from:
            if update_from == 'subnet':
                from_id = data[TAG_FROM_ID]
                fixed_ips = this_res['properties']['fixed_ips']
                for fixed_ip in fixed_ips:
                    subnet_id = fixed_ip['subnet_id']
                    if isinstance(subnet_id, str):
                        if subnet_id == self.updated_resources[from_id]['id']:
                            fixed_ip['ip_address'] = ''
                    elif isinstance(subnet_id, dict):
                        if subnet_id.get('get_resource', None):
                            if subnet_id['get_resource'] == from_id:
                                fixed_ip['ip_address'] = ''
                        elif subnet_id.get('get_param', None):
                            p_sn_id = this_res.get('parameters', {})\
                                .get(subnet_id['get_param'], {})\
                                .get('default', None)
                            if not p_sn_id:
                                raise Exception
                            if p_sn_id \
                                    == self.updated_resources[from_id]['id']:
                                fixed_ip['ip_address'] = ''

                this_res['properties']['fixed_ips'] = fixed_ips
                this_res[TAG_UPDATED] = True
                self.update_resource.update({
                    res_id: dict({TAG_RES_TYPE: res_type,
                                  TAG_RES_ID: res_id},
                                 **(this_res['properties']))})
        else:
            pass

    def _update_subnet(self):
        LOG.info("Update subnet")
        data = self.data
        res_id = self.res_id
        res_type = self.res_type
        this_res = self.updated_resources[res_id]
        if this_res.get(TAG_UPDATED, False):
            return

        update_from = data.get(TAG_FROM, None)
        if update_from:
            if update_from == 'net':
                from_id = data[TAG_FROM_ID]
                network_id = data['network_id']
                subnet_id = api.resource_detail(self.request,
                                                consts.NEUTRON_NET,
                                                network_id)['subnets'][0]
                subnet = api.resource_detail(self.request,
                                             res_type,
                                             subnet_id)
                update_data = {
                    'id': subnet['id'],
                    'properties': {
                        'name': subnet['name'],
                        'enable_dhcp': subnet['enable_dhcp'],
                        'allocation_pools': subnet['allocation_pools'],
                        'gateway_ip': subnet['gateway_ip'],
                        'ip_version': subnet['ip_version'],
                        'cidr': subnet['cidr']
                    },
                    TAG_UPDATED: True
                }
                this_res.update(update_data)
                self.dependencies.get(res_id).update({'id': subnet['id'],
                                                      'name': subnet['name']})
                self.update_resource.update({
                    res_id: dict({TAG_RES_TYPE: res_type,
                                  TAG_RES_ID: res_id,
                                  'id': subnet['id'],
                                  'name': subnet['name']},
                                 **(update_data['properties']))})
                dependent_items = self._dependent_items(excepts=[from_id])
                for key, value in dependent_items.items():
                    data = {TAG_RES_TYPE: value['type'],
                            TAG_RES_ID: key,
                            TAG_FROM: 'subnet',
                            TAG_FROM_ID: res_id}
                    if value['type'] == consts.NEUTRON_NET:
                        data['subnet_id'] = subnet['id']
                    elif value['type'] == consts.NEUTRON_PORT:
                        data['subnet_id'] = subnet['id']
                    self.execute(data)
        else:
            new_subnet_id = data['id']
            subnet = api.resource_detail(self.request,
                                         res_type,
                                         new_subnet_id)
            update_data = {
                'id': new_subnet_id,
                'properties': {
                    'name': subnet['name'],
                    'enable_dhcp': subnet['enable_dhcp'],
                    'allocation_pools': subnet['allocation_pools'],
                    'gateway_ip': subnet['gateway_ip'],
                    'ip_version': subnet['ip_version'],
                    'cidr': subnet['cidr']
                },
                TAG_UPDATED: True
            }
            this_res.update(update_data)
            self.dependencies.get(res_id).update({'id': new_subnet_id,
                                                  'name': subnet['name']})
            self.update_resource.update({
                res_id: dict({TAG_RES_TYPE: res_type,
                              TAG_RES_ID: res_id,
                              'id': new_subnet_id,
                              'name': subnet['name']},
                             **(update_data['properties']))})
            dependent_items = self._dependent_items()
            for key, value in dependent_items.items():
                data = {TAG_RES_TYPE: value['type'],
                        TAG_RES_ID: key,
                        TAG_FROM_ID: res_id,
                        TAG_FROM: 'subnet'}
                if value['type'] == consts.NEUTRON_NET:
                    data['subnet_id'] = new_subnet_id
                    if subnet['network_id'] == value['id']:
                        continue
                elif value['type'] == consts.NEUTRON_PORT:
                    data['subnet_id'] = new_subnet_id
                self.execute(data)

    def _modify_subnet_src(self, res_id, network_id):
        subnet_items = []
        for key, value in self.dependencies.items():
            if res_id in value['dependencies'] \
                    and value['type'] == consts.NEUTRON_SUBNET:
                subnet_items.append(key)
        for item in subnet_items:
            self.updated_resources[item]['from_network_id'] = network_id
            self.update_resource[item]['from_network_id'] = network_id

    def _update_net(self):
        LOG.info("Update network")
        data = self.data
        res_id = self.res_id
        res_type = self.res_type
        this_res = self.updated_resources[res_id]
        if this_res.get(TAG_UPDATED, False):
            return

        update_from = data.get(TAG_FROM, None)
        if update_from:
            from_id = data[TAG_FROM_ID]
            if update_from == 'subnet':
                subnet_id = data['subnet_id']
                subnet = api.resource_detail(self.request,
                                             consts.NEUTRON_SUBNET,
                                             subnet_id)
                network_id = subnet['network_id']
                network = api.resource_detail(self.request,
                                              res_type,
                                              network_id)
                update_data = {
                    'properties': {
                        'shared': network['shared'],
                        'admin_state_up': network['admin_state_up'],
                        'value_specs': {
                            'router:external': network['router:external'],
                            'provider:network_type':
                                network['provider:network_type'],
                            'provider:physical_network':
                                network['provider:physical_network'],
                            'provider:segmentation_id':
                                network['provider:segmentation_id']
                        },
                        'name': network['name']
                    },
                    'id': network_id,
                    TAG_UPDATED: True
                }
                this_res.update(update_data)
                self.dependencies.get(res_id).update({'id': network['id'],
                                                      'name': network['name']})
                self.update_resource.update({
                    res_id: dict({TAG_RES_TYPE: res_type,
                                  TAG_RES_ID: res_id,
                                  'id': network_id,
                                  'name': network['name']},
                                 **(update_data['properties']))})
                dependent_items = self._dependent_items(excepts=[from_id])
                for key, value in dependent_items.items():
                    data = {TAG_RES_TYPE: value['type'],
                            TAG_RES_ID: key,
                            TAG_FROM: 'net',
                            TAG_FROM_ID: res_id}
                    if value['type'] == consts.NEUTRON_SUBNET:
                        data['network_id'] = network_id
                    self.execute(data)
                self._modify_subnet_src(res_id, network_id)
        else:
            network_id = data['id']
            network = api.net_get(self.request, network_id)

            update_data = {
                'properties': {
                    'shared': network['shared'],
                    'admin_state_up': network['admin_state_up'],
                    'value_specs': {
                        'router:external': network['router:external'],
                        'provider:network_type':
                            network['provider:network_type'],
                        'provider:physical_network':
                            network['provider:physical_network'],
                        'provider:segmentation_id':
                            network['provider:segmentation_id']},
                    'name': network['name']
                },
                'id': network_id,
                TAG_UPDATED: True
            }

            this_res.update(update_data)
            self.dependencies.get(res_id).update({'id': network_id,
                                                  'name': network['name']})
            self.update_resource.update({
                res_id: dict({TAG_RES_TYPE: res_type,
                              TAG_RES_ID: res_id,
                              'id': network_id,
                              'name': network['name']},
                             **(update_data['properties']))})

            dependent_items = self._dependent_items()
            for key, value in dependent_items.items():
                data = {TAG_RES_TYPE: value['type'],
                        TAG_RES_ID: key,
                        TAG_FROM: 'net',
                        TAG_FROM_ID: res_id}
                if value['type'] == consts.NEUTRON_SUBNET:
                    data['network_id'] = network_id
                self.execute(data)

            self._modify_subnet_src(res_id, network_id)

    def _update_securitygroup(self):
        LOG.info("Update security group")
        data = self.data
        res_id = self.res_id
        res_type = self.res_type
        this_res = self.updated_resources[res_id]

        def _build_rules(rules):
            brules = []
            dependencies = []
            for rule in rules:
                if rule.get('protocol') == 'any':
                    del rule['protocol']
                # Only extract secgroups in first level,
                # ignore the dependent secgroup.
                rg_id = rule.get('remote_group_id')
                if rg_id is not None:
                    rule['remote_mode'] = "remote_group_id"
                    if rg_id == rule.get('security_group_id'):
                        del rule['remote_group_id']

                del rule['tenant_id']
                del rule['id']
                del rule['security_group_id']
                rule = dict((k, v) for k, v in rule.items() if v is not None)
                brules.append(rule)
            return brules, dependencies

        if this_res.get(TAG_UPDATED, False):
            return

        update_from = data.get(TAG_FROM, None)
        if update_from:
            pass
        else:
            sg_id = data.pop('id', None)

            # If security group id changed, then update this_res.
            if sg_id:
                new_sg = api.sg_get(self.request, sg_id)
                rules = _build_rules(new_sg.security_group_rules)[0]

                update_data = {
                    'id': sg_id,
                    TAG_UPDATED: True,
                    'properties': {'name': new_sg.name,
                                   'description': new_sg.description,
                                   'rules': rules}
                }
                this_res.update(update_data)
                self.dependencies.get(res_id).update({'id': sg_id,
                                                      'name': new_sg.name})
                update_data = {res_id: dict({TAG_RES_TYPE: res_type,
                                             TAG_RES_ID: res_id,
                                             'id': sg_id},
                                            **(this_res['properties']))}
                self.update_resource.update(update_data)

            # Is there some rule items need to be delete.
            del_rule_ids = data.pop('del_rule_ids', None)
            if del_rule_ids:
                del_rule_ids = del_rule_ids.split(" ")
                pass

    def _update_floatingip(self):
        LOG.info("Update floating ip")
        data = self.data
        res_id = self.res_id
        res_type = self.res_type
        this_res = self.updated_resources[res_id]
        if this_res.get(TAG_UPDATED, False):
            return

        update_from = data.get(TAG_FROM, None)
        if update_from:
            pass
        else:
            fip_id = data['id']
            update_data = {'id': fip_id,
                           TAG_UPDATED: True}
            this_res.update(update_data)
            self.dependencies.get(res_id).update({'id': fip_id})
            update_data = {res_id: dict({TAG_RES_TYPE: res_type,
                                         TAG_RES_ID: res_id,
                                         'id': fip_id},
                                        **(this_res['properties']))}
            self.update_resource.update(update_data)


def update_return_resource(res_src, res_update_data, dep_src, dep_update_data):
    for key, value in res_update_data.items():
            if TAG_UPDATED in value:
                value.pop(TAG_UPDATED)
                # del value[TAG_UPDATED]
                res_src.update({key: value})
                dep_src.update({key: dep_update_data[key]})
            elif ACTION_KEY in value:
                res_src.update({key: value})
                dep_src.update({key: dep_update_data[key]})
    return res_src, dep_src

    # dep_src = dict([(key, dep_update_data[key]) for key in res_src.keys()])
    # for key, value in res_update_data.items():
    #     action = value.get(ACTION_KEY, '')
    #     if action == ACTION_ADD:
    #         dep_src[key] = dep_update_data[key]
    #     # elif action == ACTION_DELETE:
    #     #     dep_src.pop(key, None)
    # return res_src, dep_src
