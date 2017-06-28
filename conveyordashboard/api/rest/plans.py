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

import json

from django.views import generic

from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils

from oslo_log import log as logging

from conveyordashboard.api import api
from conveyordashboard.plans import resources

LOG = logging.getLogger(__name__)


@urls.register
class Plans(generic.View):
    url_regex = r'conveyor/plans/$'

    @rest_utils.ajax()
    def get(self, request):
        search_opts, kwargs = rest_utils.parse_filters_kwargs(request)
        plans, _, _ = api.plan_list(request, search_opts=search_opts)
        return {'items': [p.to_dict() for p in plans]}

    @rest_utils.ajax(data_required=True)
    def post(self, request):
        data = request.DATA
        LOG.info("@@@data %s", data)
        plan = api.plan_create(request,
                               data['plan_type'],
                               data['clone_obj'],
                               plan_name=data.get('plan_name'))
        return plan.to_dict()


@urls.register
class ResourceDetailFromPlan(generic.View):
    container = 'plans/res_detail/_balloon_container.html'
    url_regex = r'conveyor/plans/(?P<plan_id>[^/]+)/detail_resource/' \
                r'(?P<res_id>[^/]+)/$'

    @rest_utils.ajax()
    def post(self, request, plan_id, res_id):
        res_type = request.DATA['resource_type']
        update_data = request.DATA
        res_view = resources.DetailResourceView(
            request, plan_id, res_type, res_id,
            update_data).render()
        return {'data': res_view,
                'image': api.get_resource_image(res_type, 'red')}


@urls.register
class BuildResourceTopo(generic.View):
    url_regex = r'conveyor/plans/(?P<plan_id>[^/]+)/build_resources_topo/$'

    @rest_utils.ajax()
    def get(self, request, plan_id):
        search_opts, kwargs = rest_utils.parse_filters_kwargs(
            request, ['availability_zone_map'])
        az_map = json.loads(kwargs['availability_zone_map'])
        return {'topo': api.build_resources_topo(request, plan_id, az_map)}
