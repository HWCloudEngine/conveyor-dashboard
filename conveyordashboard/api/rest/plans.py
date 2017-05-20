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

LOG = logging.getLogger(__name__)


@urls.register
class Index(generic.View):
    """API for test"""
    url_regex = r'conveyor/index$'

    @rest_utils.ajax()
    def get(self, request):
        return {'result': 'test for rest api'}


@urls.register
class Test(generic.View):
    """API for test"""
    url_regex = r'conveyor/test/(?P<plan>[^/]+)$'

    @rest_utils.ajax()
    def get(self, request, plan):
        LOG.info("test2: %s %s", plan, request.__dict__)
        return {'result': 'test2 for rest api'}

    @rest_utils.ajax()
    def post(self, request, plan):
        LOG.info("test2: %s %s", plan, request.__dict__)
        return {'result': 'test2 for rest api'}


@urls.register
class Update(generic.View):
    """API for obtaining detail resource"""
    url_regex = r'conveyor/plans/(?P<plan>[^/]+)/update/$'

    @rest_utils.ajax()
    def post(self, request, plan):
        return {}


@urls.register
class Cancel(generic.View):
    url_regex = r'conveyor/plans/(?P<plan>[^/]+)/cancel/$'

    @rest_utils.ajax()
    def post(self, request, plan):
        LOG.info("Delete plan %s", plan)
        api.plan_delete(request, plan)
        return {}


@urls.register
class UpdateServer(generic.View):
    """API for update plan server resource"""
    url_regex = r'conveyor/plans/(?P<plan_id>[^/+])/server/(?P<res_id>[^/]+)$'

    @rest_utils.ajax()
    def get(self, request, plan_id, res_id):
        LOG.info("Update plan server: %s, %s, %s", plan_id, res_id, request.__dict__)
        return {'result': 'success'}

    @rest_utils.ajax()
    def post(self, request, plan_id, res_id):
        LOG.info("Update plan server: %s %s %s", plan_id, res_id, request.POST)
        return {}
