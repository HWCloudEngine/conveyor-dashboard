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

from horizon import exceptions
from horizon import views
from oslo_log import log as logging

from conveyordashboard.api import api
from conveyordashboard.common import constants as consts
from conveyordashboard.common import resource_state
from conveyordashboard.plans import tables as plan_tables
from conveyordashboard.topology import topology

LOG = logging.getLogger(__name__)


class IndexView(views.HorizonTemplateView):
    page_title = _("Overview")
    template_name = 'overview_availability_zone/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)

        availability_zone = self.request.GET.get('availability_zone', None)
        try:
            azs = api.availability_zone_list(self.request)
            if availability_zone not in [az.zoneName for az in azs]:
                availability_zone = azs[0].zoneName
        except Exception as e:
            azs = []
            exceptions.handle(self.request,
                              _("Unable to retrieve availability zones."))

        context['azs'] = azs
        context['availability_zone'] = availability_zone

        # TODO(drngsl) Supposing plan type is clone
        plan_type = consts.CLONE
        plan_name = '%s#%s' % (self.request.user.tenant_id, availability_zone)

        plan = None

        try:
            for p in api.plan_list(self.request,
                                   search_opts={'plan_name': plan_name}):
                if plan_name == p.plan_name \
                        and p.plan_status in ('initiating', 'creating',
                                              'available', 'finished'):
                    plan = api.plan_get(self.request, p.plan_id)
                    break
        except Exception as e:
            LOG.error("search plan failed. %s", e)
            exceptions.handle(self.request,
                              _("Unable to retrieve plan list."))

        if plan is None:
            servers = self._get_instances_data()
            servers_id_dict = self._extract_server_ids(servers,
                                                       availability_zone,
                                                       plan_type)

            # TODO(drngsl) Need to check id_dict's length is 0 or not, if true,
            # return context, and make sure html
            # template is correct for js executing without any error or
            # exceptions(Mainly for drawing topology).
            if not servers_id_dict:
                return context

            try:
                # TODO(drngsl) First, check plan with plan_name is existing,
                # if not, create a new plan.
                plan = api.plan_create(
                    self.request, plan_type, servers_id_dict,
                    plan_name=plan_name,
                    plan_level='availability_zone:%s' % availability_zone)
            except Exception as e:
                LOG.error("Create plan failed. %s", e)
                exceptions.handle(self.request,
                                  _("Create plan fialed."))

        context['plan'] = plan

        if plan is not None:
            d3_data = topology.load_plan_d3_data(self.request, plan, plan_type)

            plan_deps_table = plan_tables.PlanDepsTable(
                self.request,
                plan_tables.trans_plan_deps(plan.original_dependencies),
                plan_id=plan.plan_id,
                plan_type=plan_type)
            context['plan_deps_table'] = plan_deps_table.render()
            context['d3_data'] = d3_data
        return context

    def _get_instances_data(self):
        instances = []
        try:
            instances = api.resource_list(self.request, consts.NOVA_SERVER)
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve instances list."))
        return instances

    def _extract_server_ids(self, servers, az_name, plan_type):
        res_ids = []
        if plan_type == consts.CLONE:
            allow_state = resource_state.INSTANCE_CLONE_STATE
        else:
            allow_state = resource_state.INSTANCE_MIGRATE_STATE
        for res in servers:
            if res.status in allow_state \
                    and getattr(res, 'OS-EXT-AZ:availability_zone',
                                None) == az_name:
                res_ids.append({'type': consts.NOVA_SERVER, 'id': res.id})
        return res_ids
