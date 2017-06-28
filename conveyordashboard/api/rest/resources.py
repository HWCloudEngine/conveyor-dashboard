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

from django.views import generic
from openstack_dashboard import api as os_api
from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils

from conveyordashboard.api import api
from conveyordashboard.security_groups.tables import RulesTable
from conveyordashboard.security_groups import utils as secgroup_utils

from oslo_log import log
LOG = log.getLogger(__name__)


@urls.register
class Resource(generic.View):
    url_regex = r'conveyor/resources/(?P<res_type>[^/]+)/(?P<res_id>[^/]+)/$'

    @rest_utils.ajax()
    def get(self, request, res_type, res_id):
        return api.resource_get(request, res_type, res_id)


@urls.register
class Resources(generic.View):
    url_regex = r'conveyor/resources/(?P<resource_type>[^/]+)/$'

    @rest_utils.ajax()
    def get(self, request, resource_type):
        search_opts, kwargs = rest_utils.parse_filters_kwargs(request)
        res = api.resource_list(request, resource_type,
                                search_opts=search_opts)
        return {'items': [r.__dict__.get('_info') for r in res]}


@urls.register
class CreateRule(generic.View):
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
