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

from django.utils.translation import ugettext_lazy as _
from horizon import tabs
from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = 'overview'
    template_name = 'plans/_detail_overview.html'

    def get_context_data(self, request):
        plan = self.tab_group.kwargs['plan']
        return {
            'plan': plan
        }


class TopologyTab(tabs.Tab):
    name = _("Topology")
    slug = 'topology'
    template_name = 'plans/_detail_topology.html'
    preload = False

    def get_context_data(self, request):
        context = {}
        plan = self.tab_group.kwargs['plan']
        context['plan_id'] = plan.plan_id
        context['d3_data'] = '[]'
        return context


class DetailTabs(tabs.TabGroup):
    slug = 'plan_details'
    tabs = (OverviewTab,)
