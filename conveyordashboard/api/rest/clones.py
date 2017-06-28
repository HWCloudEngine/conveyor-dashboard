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
class Clones(generic.View):
    url_regex = r'conveyor/clones/(?P<plan_id>[^/]+)/$'

    @rest_utils.ajax(data_required=True)
    def post(self, request, plan_id):
        data = request.DATA
        api.clone(request, plan_id,
                  data.get('availability_zone_map'),
                  data.get('clone_resources'),
                  update_resources=data.get('update_resources'),
                  replace_resources=data.get('replace_resources'),
                  clone_links=data.get('clone_links'),
                  sys_clone=data.get('sys_clone'),
                  copy_data=data.get('copy_data'))
        return {}
