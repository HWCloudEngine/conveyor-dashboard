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

from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils

from oslo_log import log as logging

from conveyordashboard.api import api
from conveyordashboard.topology import tables as topology_tables

LOG = logging.getLogger(__name__)


@urls.register
class ResourceDetail(generic.View):
    """API for obtaining detail resource"""

    url_regex = r'conveyor/resources/(?P<res_type>[^/]+)/(?P<res_id>[^/]+)/$'

    @rest_utils.ajax(data_required=True)
    def post(self, request, res_type, res_id):
        return {'code': '200'}
        # POST = request.POST
        # # LOG.info("res_detail request.POST: %s", POST)
        # plan_id = POST['plan_id']
        # is_original = strutils.bool_from_string(POST.get('is_original', False))
        #
        # resource_type = POST['resource_type']
        # resource_id = POST['resource_id']
        # update_data = json.JSONDecoder().decode(POST['update_data'])
        # updated_res = json.JSONDecoder().decode(POST['updated_res'])
        # data = resources.ResourceDetailFromPlan(
        #     request, plan_id, resource_type, resource_id,
        #     update_data, updated_res, is_original).render()
        # resp = {'msg': 'success',
        #         'data': data,
        #         'image': api.get_resource_image(resource_type, 'red')}
        # return http.HttpResponse(json.dumps(resp),
        #                          content_type='application/json')


@urls.register
class SecurityGroupRules(generic.View):

    url_regex = r'conveyor/resources/secgroup/(?P<secgroup_id>[^/]+)/rules/$'

    @rest_utils.ajax()
    def get(self, request, secgroup_id):
        sg = api.sg_get(request, secgroup_id)
        rules_table = topology_tables.RulesTable(request, sg.rules)
        return {'rules': rules_table.render()}


@urls.register
class CreateSecurityGroupRules(generic.View):

    url_regex = r'conveyor/resources/secgroup/(?P<secgroup_id>[^/]+)/rules/' \
                r'create/$'

    @rest_utils.ajax()
    def post(self, request, secgroup_id):
        return {}
