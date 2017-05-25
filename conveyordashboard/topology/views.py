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

from django.core.urlresolvers import reverse
from django import http
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from horizon import exceptions
from horizon import forms
from openstack_dashboard import api as os_api
from openstack_dashboard.utils import filters
from oslo_log import log as logging

from conveyordashboard.api import api
from conveyordashboard.common import constants
from conveyordashboard.topology import forms as topology_forms
from conveyordashboard.topology import tables as topology_tables
from conveyordashboard.topology import topology
from conveyordashboard.topology import utils as topology_utils

LOG = logging.getLogger(__name__)


class SecgroupRulesView(View):
    @staticmethod
    def get(request, **kwargs):
        sg_id = kwargs['secgroup_id']
        sg = api.sg_get(request, sg_id)
        rules_table = topology_tables.RulesTable(request, sg.rules)
        return http.HttpResponse(rules_table.render(),
                                 content_type='text/html')


class AddRuleView(forms.ModalFormView):
    form_class = topology_forms.AddRule
    form_id = 'create_security_group_rule_form'
    modal_header = _("Add Rule")
    modal_id = 'create_security_group_rule_modal'
    template_name = 'topology/add_rule.html'
    ajax_template_name = 'topology/add_rule.html'
    submit_label = _("Add")
    submit_url = "horizon:conveyor:plans:add_rule"
    url = "horizon:conveyor:plans:index"
    page_title = _("Add Rule")

    def get_success_url(self):
        return reverse(self.url)

    def get_context_data(self, **kwargs):
        context = super(AddRuleView, self).get_context_data(**kwargs)
        LOG.info("request Type: %s", self.request.is_ajax())
        context["security_group_id"] = self.kwargs['security_group_id']
        args = (self.kwargs['security_group_id'],)
        context['submit_url'] = reverse(self.submit_url, args=args)
        context['cancel_url'] = reverse(self.url)
        return context

    def get_initial(self):
        return {'id': self.kwargs['security_group_id']}

    def get_form_kwargs(self):
        kwargs = super(AddRuleView, self).get_form_kwargs()

        try:
            tenant_id = self.request.user.tenant_id
            groups = api.sg_list(self.request, tenant_id=tenant_id)
        except Exception:
            groups = []
            exceptions.handle(self.request,
                              _("Unable to retrieve security groups."))

        security_groups = []
        for group in groups:
            if group.id == filters.get_int_or_uuid(
                    self.kwargs['security_group_id']):
                security_groups.append((group.id,
                                        _("%s (current)") % group.name))
            else:
                security_groups.append((group.id, group.name))
        kwargs['sg_list'] = security_groups
        return kwargs


class CreateRuleView(View):
    @staticmethod
    def post(request, **kwargs):
        POST = request.POST
        LOG.info("CreateRuleView: {0} {1}".format(request.POST, kwargs))
        sg_rule_param = json.JSONDecoder().decode(POST['secgroup_rule'])
        LOG.info("sg_rule_param: %s", sg_rule_param)
        LOG.info("sg_rule_param after clean: %s", sg_rule_param)

        if sg_rule_param.get('port', None):
            sg_rule_param['port'] = int(sg_rule_param['port'])
        if sg_rule_param.get('from_port', None):
            sg_rule_param['from_port'] = int(sg_rule_param['from_port'])
        if sg_rule_param.get('to_port', None):
            sg_rule_param['to_port'] = int(sg_rule_param['to_port'])

        rule = topology_utils.generate_rule(sg_rule_param)

        def rebuild_rules(r):
            def_r = {'remote_ip_prefix': None, 'remote_group_id': None,
                     'ethertype': None, 'security_group_id': None,
                     'direction': None, 'protocol': None,
                     'port_range_min': None, 'port_range_max': None}
            return dict(def_r, **r)
        sgr = os_api.neutron.SecurityGroupRule(rebuild_rules(rule))
        rules_table = topology_tables.RulesTable(request, [sgr])
        resp_data = {'sgr': rule,
                     'sgr_html': rules_table.render()}
        return http.HttpResponse(json.dumps(resp_data),
                                 content_type='application/json')


def clean_deps(deps):
    for res_id, dep in deps.items():
        dep['dependencies'] = [dep_id for dep_id in dep['dependencies']
                               if dep_id in deps]


def filter_deps(request, plan_id, plan_type, deps, res_id=None):
    plan = api.plan_get(request, plan_id)
    plan_deps = plan.updated_dependencies \
        if plan_type == 'clone' else plan.original_dependencies
    plan_deps.update(deps)
    for k, v in plan_deps.items():
        if v.get(constants.RES_ACTION_KEY, '') == constants.ACTION_DELETE:
            plan_deps.pop(k)

    if res_id is not None:
        local_deps = dict()
        local_deps[res_id] = plan_deps[res_id]
        for key, value in plan_deps.items():
            if key in plan_deps[res_id]['dependencies'] \
                    or res_id in value['dependencies']:
                local_deps[key] = value
        return local_deps
    return plan_deps


class LocalTopologyView(View):
    @staticmethod
    def get(request, **kwargs):
        GET = request.GET
        plan_id = GET['plan_id']
        plan_type = GET['plan_type']
        res_id = GET['res_id']
        local_deps = filter_deps(request, plan_id, plan_type, {}, res_id)
        d3_data = topology.load_d3_data(request, plan_id, local_deps)
        return http.HttpResponse(d3_data,
                                 content_type='application/json')

    @staticmethod
    def post(request, **kwargs):
        POST = request.POST
        param = POST['param']
        deps = json.JSONDecoder().decode(POST['deps'])
        params = dict([(p.split('=')[0], p.split('=')[1])
                       for p in param.split('&')])
        plan_id = params['plan_id']
        plan_type = params['plan_type']
        res_id = params['res_id']
        local_deps = filter_deps(request, plan_id, plan_type, deps, res_id)
        d3_data = topology.load_d3_data(request, plan_id, local_deps)
        return http.HttpResponse(d3_data,
                                 content_type='application/json')


class GlobalTopologyView(View):
    @staticmethod
    def get(request, **kwargs):
        GET = request.GET
        plan_id = GET['plan_id']
        plan_type = GET['plan_type']
        plan = api.plan_get(request, plan_id)
        d3_data = topology.load_plan_d3_data(request,
                                             plan,
                                             plan_type)

        return http.HttpResponse(d3_data,
                                 content_type='application/json')

    @staticmethod
    def post(request, **kwargs):
        POST = request.POST
        param = POST['param']
        deps = json.JSONDecoder().decode(POST['deps'])
        params = dict([(p.split('=')[0], p.split('=')[1])
                       for p in param.split('&')])
        plan_id = params['plan_id']
        plan_type = params['plan_type']
        global_deps = filter_deps(request, plan_id, plan_type, deps)
        d3_data = topology.load_d3_data(request, plan_id, global_deps)
        return http.HttpResponse(d3_data,
                                 content_type='application/json')
