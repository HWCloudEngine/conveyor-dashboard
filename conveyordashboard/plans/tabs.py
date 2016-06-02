# Copyright 2012 Nebula, Inc.
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

import logging
import uuid

from django.template import loader
from django.utils.translation import ugettext_lazy as _

from horizon import tabs

from conveyordashboard.api import api
from conveyordashboard.constant import RESOURCE_TYPE
from conveyordashboard.topology import topology

OVERVIEW_ITEMS_DIR = 'plans/overview_items/'
OVERVIEW_ITEMTEMPL_PATH = 'plans/overview_items/itemtmpl.html'

LOG = logging.getLogger(__name__)


def render_overview_html(plan):
    overview_html = {}
    for template_name, data in plan.items():
        type = data[RESOURCE_TYPE]
        image = api.get_resource_image(type)
        template_html = OVERVIEW_ITEMS_DIR \
                        + type.split("::")[-1].lower() + '.html'
        params=data.pop("parameters")
        propers = data.pop("properties")
        overview_html[template_name] = \
                loader.render_to_string(OVERVIEW_ITEMTEMPL_PATH,
                                        {'template_html': template_html,
                                         'image': image,
                                         'type': str(uuid.uuid4()),
                                         'data': data,
                                         'params': params,
                                         'propers': propers})
    return overview_html


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = ("plans/_detail_overview.html")

    def get_context_data(self, request):
        plan = self.tab_group.kwargs['plan']
        original_resources_html = self.get_render_html(plan.original_resources)
        plan.original_resources = original_resources_html
        updated_resources_html = self.get_render_html(plan.updated_resources)
        plan.updated_resources = updated_resources_html
        return {"plan": plan}

    def get_render_html(self, plan):
        return render_overview_html(plan)


class TopologyTab(tabs.Tab):
    name = _("Topology")
    slug = "topology"
    template_name = ("plans/_detail_topology.html")
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
    slug = "plan_details"
    tabs = (OverviewTab, TopologyTab)
