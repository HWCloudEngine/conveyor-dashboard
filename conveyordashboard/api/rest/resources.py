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

from django import http
from django.views import generic
from openstack_dashboard import api as os_api
from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils

from conveyordashboard.api import api
from conveyordashboard.common import constants as consts
from conveyordashboard.floating_ips.tables import FloatingIPsTable
from conveyordashboard.instances.tables import InstancesTable
from conveyordashboard.loadbalancers.tables import PoolsTable
from conveyordashboard.networks.tables import NetworksTable
from conveyordashboard.security_groups.tables import RulesTable
from conveyordashboard.security_groups.tables import SecurityGroupsTable
from conveyordashboard.security_groups import utils as secgroup_utils
from conveyordashboard.volumes.tables import VolumesTable

TYPE_CLASS_MAPPING = {
    consts.NOVA_SERVER: InstancesTable,
    consts.CINDER_VOLUME: VolumesTable,
    consts.NEUTRON_POOL: PoolsTable,
    consts.NEUTRON_NET: NetworksTable,
    consts.NEUTRON_FLOATINGIP: FloatingIPsTable,
    consts.NEUTRON_SECGROUP: SecurityGroupsTable
}


@urls.register
class RowActionsView(generic.View):
    url_regex = r'conveyor/resources/(?P<resource_type>[^/]+)/' \
                r'(?P<resource_id>[^/]+)/row_actions/$'

    @rest_utils.ajax()
    def get(self, request, resource_type, resource_id):
        resource_type = resource_type.replace('__', '::')
        res = api.get_wrapped_detail_resource(request,
                                              resource_type,
                                              resource_id)
        if resource_type in TYPE_CLASS_MAPPING:
            table = TYPE_CLASS_MAPPING[resource_type](request)
            actions = table.render_row_actions(res)
            return http.HttpResponse(actions, content_type='text/html')


@urls.register
class TableActionsView(generic.View):
    url_regex = r'conveyor/resources/(?P<resource_type>[^/]+)/table_actions/$'

    @rest_utils.ajax()
    def get(self, request, resource_type):
        resource_type = resource_type.replace('__', '::')
        if resource_type in TYPE_CLASS_MAPPING:
            table = TYPE_CLASS_MAPPING[resource_type](request)
            table_actions = table.render_table_actions()
            return http.HttpResponse(table_actions, content_type='text/html')


@urls.register
class CreateRuleView(generic.View):
    url_regex = r'conveyor/resources/create_rule/$'

    @rest_utils.ajax()
    def post(self, request):
        rule_params = request.DATA

        if rule_params.get('port', None):
            rule_params['port'] = int(rule_params['port'])
        if rule_params.get('from_port', None):
            rule_params['from_port'] = int(rule_params['from_port'])
        if rule_params.get('to_port', None):
            rule_params['to_port'] = int(rule_params['to_port'])

        rule = secgroup_utils.generate_rule(rule_params)

        def rebuild_rules(r):
            def_r = {'remote_ip_prefix': None, 'remote_group_id': None,
                     'ethertype': None, 'security_group_id': None,
                     'direction': None, 'protocol': None,
                     'port_range_min': None, 'port_range_max': None}
            return dict(def_r, **r)
        sgr = os_api.neutron.SecurityGroupRule(rebuild_rules(rule))
        rules_table = RulesTable(request, [sgr])
        return {
            'sgr': rule,
            'sgr_html': rules_table.render()
        }
