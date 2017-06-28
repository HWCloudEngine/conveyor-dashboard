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
from oslo_utils import strutils

from conveyordashboard.api import api
from conveyordashboard.common import constants
from conveyordashboard.plans import resources
from conveyordashboard.plans import tables as plan_tables
from conveyordashboard.topology import topology

LOG = logging.getLogger(__name__)


@urls.register
class Delete(generic.View):
    url_regex = r'conveyor/plans/(?P<plan_id>[^/]+)/delete/$'

    @rest_utils.ajax()
    def post(self, request, plan_id):
        api.plan_delete(request, plan_id)
        return {}


@urls.register
class ResourceDetailFromPlan(generic.View):
    url_regex = r'conveyor/plans/(?P<plan_id>[^/]+)/detail_resource/' \
                r'(?P<resource_id>[^/]+)/$'

    @rest_utils.ajax()
    def post(self, request, plan_id, resource_id):
        is_original = strutils.bool_from_string(request.DATA.get('is_original',
                                                                 False))

        resource_type = request.DATA['resource_type']
        update_data = request.DATA['update_data']
        updated_res = request.DATA['updated_res']
        data = resources.ResourceDetailFromPlan(
            request, plan_id, resource_type, resource_id,
            update_data, updated_res, is_original).render()
        return {'data': data,
                'image': api.get_resource_image(resource_type, 'red')}


@urls.register
class UpdatePlanResourceFrontend(generic.View):
    url_regex = r'conveyor/plans/(?P<plan_id>[^/]+)/' \
                r'update_plan_resource_frontend/$'

    @rest_utils.ajax()
    def post(self, request, plan_id):
        # Updated_resources
        i_updated_resources = request.DATA['updated_resources']
        # updated_resources = plan.updated_resources
        updated_resources = api.update_resources(request, plan_id,
                                                 with_deps=False)
        updated_resources.update(i_updated_resources)

        # Dependenies
        i_dependencies = request.DATA['dependencies']
        dependencies = api.update_dependencies(request, plan_id,
                                               with_deps=False)
        dependencies.update(i_dependencies)

        data = request.DATA['data']

        # Update res
        update_res = request.DATA['update_res']
        update_resource = dict([(ur[constants.TAG_RES_ID], ur)
                                for ur in update_res])

        for k, v in update_resource.items():
            if 'name' in v:
                updated_resources[k]['properties']['name'] = v['name']

        planupdate = resources.PlanUpdate(request,
                                          plan_id,
                                          updated_resources,
                                          dependencies,
                                          update_resource=update_resource)

        # Execute update resource items of plan
        planupdate.execute(data)

        (ret_reses, ret_deps, ret_res) = planupdate.execute_return()

        resources.update_return_resource(i_updated_resources,
                                         ret_reses,
                                         i_dependencies,
                                         ret_deps)

        for k, v in ret_deps.items():
            v['name'] = ret_reses[k]['properties'].get('name', None)
        deps = dict([(key, value) for key, value in dependencies.items()
                     if value.get(constants.RES_ACTION_KEY,
                                  '') != constants.ACTION_DELETE])

        res_deps = plan_tables.PlanDepsTable(
            request,
            plan_tables.trans_plan_deps(deps),
            plan_id=plan_id,
            plan_type=constants.CLONE).render()

        d3_data = topology.load_d3_data(request, deps)

        return {
            'd3_data': d3_data,
            'res_deps': res_deps,
            'update_resources': ret_res.values(),
            'updated_resources': i_updated_resources,
            'dependencies': i_dependencies
        }
