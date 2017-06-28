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

import collections

from django.template import loader
from django.utils.translation import ugettext_lazy as _
from horizon import tabs
from oslo_log import log as logging
from oslo_utils import uuidutils

from conveyordashboard.api import api
from conveyordashboard.common import constants
from conveyordashboard.topology import topology

OVERVIEW_ITEMS_DIR = 'plans/overview_items/'
OVERVIEW_ITEMTEMPL_PATH = 'plans/overview_items/itemtmpl.html'

LOG = logging.getLogger(__name__)


def render_overview_html(request, res_dict, dep_dict):
    try:
        res_dict = sorted(res_dict.iteritems(), key=lambda i: i[1]['type'])
    except Exception:
        pass

    overview_html = collections.OrderedDict()
    for (template_name, data) in res_dict:
        res_type = data['type']
        if res_type == constants.NEUTRON_NET:
            value_specs = data['properties'].get('value_specs', {})
            if value_specs:
                for k, v in value_specs.items():
                    if ':' in k:
                        nk = k.replace(':', '__')
                        value_specs[nk] = v
        elif res_type == constants.NEUTRON_FLOATINGIP:
            fid = data['id']
            fip = api.resource_detail(request,
                                      constants.NEUTRON_FLOATINGIP, fid)
            LOG.info('fip: %s', fip)
            data['properties']['floating_ip_address'] \
                = fip['floating_ip_address']

        type = data['type']
        cloned = dep_dict.get(template_name, {}).get('is_cloned', False)
        image = api.get_resource_image(type, 'gray' if cloned else 'green')
        template_html = ''.join([OVERVIEW_ITEMS_DIR,
                                 type.split('::')[-1].lower(),
                                 '.html'])
        params = data.pop('parameters')
        propers = data.pop('properties')
        context = {
            'template_html': template_html,
            'image': image,
            'type': uuidutils.generate_uuid(),
            'data': data,
            'params': params,
            'propers': propers
        }
        overview_html[template_name] = \
            loader.render_to_string(OVERVIEW_ITEMTEMPL_PATH, context)
    return overview_html


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = 'overview'
    template_name = 'plans/_detail_overview.html'

    def get_context_data(self, request):
        plan = self.tab_group.kwargs['plan']
        original_resources_html = self.get_render_html(
            plan.original_resources, plan.original_dependencies)
        plan.original_resources = original_resources_html
        updated_resources_html = self.get_render_html(
            plan.updated_resources, plan.update_dependencies)
        plan.updated_resources = updated_resources_html
        return {"plan": plan}

    def get_render_html(self, res_dict, dep_dict):
        return render_overview_html(self.request, res_dict, dep_dict)


class TopologyTab(tabs.Tab):
    name = _("Topology")
    slug = 'topology'
    template_name = 'plans/_detail_topology.html'
    preload = False

    def get_context_data(self, request):
        context = {}
        plan_id = self.tab_group.kwargs['plan_id']
        context['plan_id'] = plan_id
        plan = self.tab_group.kwargs['plan']
        context['d3_data'] = topology.load_plan_d3_data(self.request,
                                                        plan,
                                                        plan.plan_type)
        return context


class DetailTabs(tabs.TabGroup):
    slug = 'plan_details'
    tabs = (OverviewTab, TopologyTab)
