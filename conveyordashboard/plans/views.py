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
import yaml

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django import http
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from oslo_log import log as logging

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from conveyordashboard.api import api
from conveyordashboard.api import models
from conveyordashboard.common import constants
from conveyordashboard.common import tables as common_tables
from conveyordashboard.plans import forms as plan_forms
from conveyordashboard.plans import tables as plan_tables
from conveyordashboard.plans import tabs as plan_tabs
from conveyordashboard.topology import topology

LOG = logging.getLogger(__name__)


class IndexView(common_tables.PagedTableMixin, tables.DataTableView):
    table_class = plan_tables.PlansTable
    template_name = 'plans/index.html'
    page_title = _("Plans")

    @memoized.memoized_method
    def get_data(self):
        plans = []

        try:
            marker, sort_dir = self._get_marker()
            search_opts = {
                'marker': marker,
                'sort_dir': sort_dir,
                'paginate': True
            }

            plans, self._has_more_data, self._has_prev_data = \
                api.plan_list(self.request, search_opts=search_opts)

            if sort_dir == "asc":
                plans.reverse()
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve plan list."))
        for plan in plans:
            setattr(plan, 'id', plan.plan_id)
        return plans

    def get_filters(self, filters):
        filter_field = self.table.get_filter_field()
        filter_action = self.table._meta._filter_action
        if filter_action.is_api_filter(filter_field):
            filter_string = self.table.get_filter_string()
            if filter_field and filter_string:
                filters[filter_field] = filter_string
        return filters


class DetailView(tabs.TabView):
    tab_group_class = plan_tabs.DetailTabs
    template_name = 'horizon/common/_detail.html'
    redirect_url = 'horizon:conveyor:plans:index'
    page_title = "{{ plan.plan_name|default:plan.plan_id }}"

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        plan = self.get_data()
        context['plan_id'] = self.kwargs['plan_id']
        context['plan'] = plan
        context['url'] = reverse(self.redirect_url)
        table = plan_tables.PlansTable(self.request)
        context['actions'] = table.render_row_actions(plan)
        return context

    @memoized.memoized_method
    def get_data(self):
        plan_id = self.kwargs['plan_id']
        try:
            plan = api.plan_get(self.request, plan_id)
        except Exception:
            redirect = reverse(self.redirect_url)
            exceptions.handle(self.request,
                              _("Unable to retrieve details for "
                                "plan %s.") % plan_id,
                              redirect=redirect)
            raise exceptions.Http302(redirect)
        return plan

    def get_tabs(self, request, *args, **kwargs):
        plan = self.get_data()
        return self.tab_group_class(request, plan=plan, **kwargs)


def create_plan(request, plan_type, ids, plan_level=None):
    resource = []
    id_list = {}
    for item in ids.split('**'):
        id_list[item.split('*')[0]] = item.split('*')[1].split(',')
    for key, value in id_list.items():
        for id in value:
            resource.append({'type': key, 'id': id})

    return api.plan_create(request, plan_type, resource, plan_level=plan_level)


class CloneView(forms.ModalFormView):
    form_class = plan_forms.ClonePlan
    form_id = 'clone_plan_form'
    template_name = 'plans/clone.html'
    submit_url = reverse_lazy("horizon:conveyor:plans:clone")
    success_url = reverse_lazy("horizon:conveyor:plans:index")

    def get_context_data(self, **kwargs):
        plan = getattr(self, 'plan')
        is_original = getattr(self, 'is_original')

        self.modal_header = _('Clone Plan %s') % plan.plan_id
        base_url = reverse('horizon:conveyor:plans:clone')
        params = urlencode({'plan_id': plan.plan_id})
        self.submit_url = '?'.join([base_url, params])

        context = super(CloneView, self).get_context_data(**kwargs)
        context['plan_id'] = plan.plan_id
        context['is_original'] = is_original

        plan_deps_table = plan_tables.PlanDepsTable(
            self.request,
            plan_tables.trans_plan_deps(plan.original_dependencies),
            plan_id=plan.plan_id,
            plan_type=constants.CLONE)
        context['plan_deps_table'] = plan_deps_table.render()

        d3_data = topology.load_plan_d3_data(self.request,
                                             plan,
                                             constants.CLONE,
                                             is_original)
        context['d3_data'] = d3_data

        return context

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        if 'ids' in self.request.GET:
            try:
                ids = self.request.GET['ids']
                plan_level = self.request.GET.get('plan_level')

                return create_plan(self.request, constants.CLONE, ids,
                                   plan_level=plan_level), True
            except Exception as e:
                LOG.error("Unable to create plan. %s", e)
                msg = _("Unable to create plan.")
                exceptions.handle(self.request, msg)
                return None, None
        elif 'plan_id' in self.request.GET:
            try:
                return (api.plan_get(self.request,
                                     self.request.GET['plan_id']),
                        False)
            except Exception as e:
                LOG.error("Unable to retrieve plan details. %s", e)
                msg = _("Unable to retrieve plan details.")
                exceptions.handle(self.request, msg)
                return None, None

        LOG.error("Query string does not contain either plan_id or "
                  "resource ids.")
        exceptions.handle(self.request,
                          _("Query string is not a correct format."))

    def get_initial(self):
        plan, is_original = self.get_object()
        setattr(self, 'plan', plan)
        setattr(self, 'is_original', is_original)

        return {
            'plan_id': plan.plan_id,
            'is_original': is_original
        }


class MigrateView(forms.ModalFormView):
    form_class = plan_forms.MigratePlan
    form_id = 'migrate_plan_form'
    modal_header = _("Migrate Plan")
    template_name = 'plans/migrate.html'
    success_url = reverse_lazy("horizon:conveyor:plans:index")

    def get_context_data(self, **kwargs):
        plan = getattr(self, 'plan')

        self.modal_header = _('Migrate Plan %s') % plan.plan_id
        base_url = reverse('horizon:conveyor:plans:migrate')
        params = urlencode({'plan_id': plan.plan_id})
        self.submit_url = '?'.join([base_url, params])

        context = super(MigrateView, self).get_context_data(**kwargs)
        context['plan_id'] = plan.plan_id

        plan_deps_table = plan_tables.PlanDepsTable(
            self.request,
            plan_tables.trans_plan_deps(plan.original_dependencies),
            plan_id=plan.plan_id,
            plan_type=constants.MIGRATE)
        context['plan_deps_table'] = plan_deps_table.render()

        d3_data = topology.load_plan_d3_data(self.request,
                                             plan,
                                             constants.MIGRATE,)
        context['d3_data'] = d3_data
        return context

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        if 'ids' in self.request.GET:
            try:
                ids = self.request.GET['ids']

                return create_plan(self.request, constants.MIGRATE, ids), True
            except Exception:
                msg = _("Query string is not a correct format.")
                exceptions.handle(self.request, msg)
                return None, None
        elif 'plan_id' in self.request.GET:
            try:
                return (api.plan_get(self.request,
                                     self.request.GET['plan_id']),
                        False)
            except Exception:
                msg = _("Unable to retrieve plan details.")
                exceptions.handle(self.request, msg)
                return None, None

        LOG.error("Query string does not contain either plan_id or "
                  "resource ids.")
        exceptions.handle(self.request,
                          _("Query string is not a correct format."))

    def get_initial(self):
        plan, is_original = self.get_object()
        setattr(self, 'plan', plan)
        setattr(self, 'is_original', is_original)

        return {
            'plan_id': plan.plan_id,
            'is_original': is_original
        }


class SaveView(forms.ModalFormView):
    """Save the edited plan that create from res directly"""

    form_class = plan_forms.SavePlan
    form_id = 'save_plan_form'
    modal_header = _("Save Plan")
    template_name = 'plans/save.html'
    submit_label = _("Save")
    success_url = reverse_lazy("horizon:conveyor:plans:index")
    page_title = _("Save")

    def get_context_data(self, **kwargs):
        submit_url = 'horizon:conveyor:plans:save'
        self.submit_url = reverse(submit_url,
                                  kwargs={'plan_id': self.kwargs['plan_id']})
        context = super(SaveView, self).get_context_data(**kwargs)
        context.update(self._show_filter(self.get_object()))
        return context

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        try:
            return api.plan_get(self.request, self.kwargs['plan_id'])
        except Exception as e:
            LOG.error("Unable to retrieve plan information. %s", e)
            msg = _("Unable to retrieve plan information.")
            exceptions.handle(self.request, msg)

    @memoized.memoized_method
    def _show_filter(self, plan):
        return show_filter(plan)

    def get_initial(self):
        plan = self.get_object(**self.kwargs)
        initial = {
            'plan_id': self.kwargs['plan_id'],
            'plan_type': plan.plan_type,
            'sys_clone': getattr(plan, 'sys_clone', False),
            'copy_data': getattr(plan, 'copy_data', True)
        }
        initial.update(show_filter(plan))
        return initial


class ModifyView(forms.ModalFormView):
    form_class = plan_forms.ModifyPlan
    form_id = 'modify_form'
    modal_header = _("Modify Plan")
    template_name = 'plans/modify.html'
    context_object_name = 'plan'
    submit_label = _("Save")
    submit_url = reverse_lazy("horizon:conveyor:plans:modify")
    success_url = reverse_lazy("horizon:conveyor:plans:index")
    page_title = _("Modify Plan")

    def get_context_data(self, **kwargs):
        context = super(ModifyView, self).get_context_data(**kwargs)
        context['plan_id'] = self.kwargs['plan_id']

        plan = self.get_object(**self.kwargs)

        context['type'] = 'clone'
        plan_deps_table = plan_tables.PlanDepsTable(
            self.request,
            plan_tables.trans_plan_deps(plan.updated_dependencies),
            plan_id=plan.plan_id,
            plan_type=constants.CLONE
        )
        context['plan_deps_table'] = plan_deps_table.render()

        d3_data = topology.load_d3_data(self.request,
                                        plan.updated_dependencies)
        context['d3_data'] = d3_data
        return context

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        try:
            return api.plan_get(self.request, kwargs['plan_id'])
        except Exception:
            redirect = ModifyView.success_url
            msg = _("Unable to retrieve plan details.")
            exceptions.handle(self.request, msg, redirect=redirect)

    def get_initial(self):
        initial = super(ModifyView, self).get_initial()
        initial.update({'plan_id': self.kwargs['plan_id']})
        return initial


class ImportView(forms.ModalFormView):
    form_class = plan_forms.ImportPlan
    form_id = 'import_plan_form'
    modal_header = _("Import Plan")
    template_name = 'plans/import.html'
    context_object_name = 'plan'
    submit_label = _("Import")
    submit_url = reverse_lazy("horizon:conveyor:plans:import")
    success_url = reverse_lazy("horizon:conveyor:plans:index")
    page_title = _("Import Plan")

    def get_context_data(self, **kwargs):
        context = super(ImportView, self).get_context_data(**kwargs)
        return context

    def get_initial(self):
        initial = super(ImportView, self).get_initial()
        return initial


class ExportView(View):
    @staticmethod
    def get(request, **kwargs):
        try:
            plan_id = kwargs['plan_id']
            plan = api.download_template(request, plan_id)
        except Exception:
            redirect = reverse("horizon:conveyor:plans:index")
            exceptions.handle(request,
                              _("Unable to export plan."),
                              redirect=redirect)
            return

        response = http.HttpResponse(content_type='application/binary')
        response['Content-Disposition'] = ('attachment; filename=plan-%s'
                                           % plan_id)
        template = yaml.dump(yaml.load(json.dumps(plan[1]['template'])))
        response.write(template)
        response['Content-Length'] = str(len(response.content))
        return response


def show_filter(plan):
    plan_type = plan.plan_type
    if plan_type == constants.CLONE:
        deps = plan.updated_dependencies
    else:
        deps = plan.original_dependencies

    show_az = False
    show_sys_clone = False
    show_copy_data = False
    for dep in deps.values():
        res_type = dep['type']
        if res_type == constants.NOVA_SERVER:
            show_az = True
            show_sys_clone = True
            show_copy_data = True
            break
        elif res_type == constants.CINDER_VOLUME:
            show_az = True
            show_copy_data = True
    return {
        'show_az': show_az,
        'show_sys_clone': show_sys_clone,
        'show_copy_data': show_copy_data
    }


class DestinationView(forms.ModalFormView):
    form_class = plan_forms.Destination
    form_id = 'destination_form'
    template_name = 'plans/destination.html'
    context_object_name = 'plan'
    success_url = reverse_lazy("horizon:conveyor:plans:index")

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        try:
            return api.plan_get(self.request, self.kwargs['plan_id'])
        except Exception:
            msg = _("Unable to retrieve plan information.")
            exceptions.handle(self.request, msg)

    @memoized.memoized_method
    def _show_filter(self, plan):
        return show_filter(plan)

    @memoized.memoized_method
    def get_plan_res_azs(self, plan):
        try:
            plan_res_azs = api.list_plan_resource_availability_zones(
                self.request, plan)
            return plan_res_azs or []
        except Exception:
            msg = _("Unable to retrieve availability zones for plan resource.")
            exceptions.handle(self.request, msg)

    def get_context_data(self, **kwargs):
        plan = self.get_object(**self.kwargs)
        plan_type = plan.plan_type
        self.submit_label = plan_type.title()
        if plan_type == constants.CLONE:
            self.modal_header = self.page_title = _('Clone Destination')
        else:
            self.modal_header = self.page_title = _('Migrate Destination')
        submit_url = 'horizon:conveyor:plans:destination'
        self.submit_url = reverse(submit_url,
                                  kwargs={'plan_id': plan.plan_id})
        context = super(DestinationView,
                        self).get_context_data(**kwargs)
        context['plan_type'] = plan_type
        context.update(self._show_filter(plan))

        res_azs = self.get_plan_res_azs(plan.plan_id)
        context['destination_az'] = plan_tables.DestinationAZTable(
            self.request,
            [models.Resource({'availability_zone': az}) for az in res_azs])
        try:
            availability_zones = api.availability_zone_list(self.request)
        except Exception:
            availability_zones = []
            exceptions.handle(self.request,
                              _("Unable to retrieve availability zones."))
        context['availability_zones'] = json.dumps(
            [az.zoneName for az in availability_zones])
        return context

    def get_initial(self):
        plan = self.get_object(**self.kwargs)
        res_azs = self.get_plan_res_azs(plan.plan_id)
        initial = {
            'plan_id': self.kwargs['plan_id'],
            'plan_type': plan.plan_type,
            'sys_clone': getattr(plan, 'sys_clone', False),
            'copy_data': getattr(plan, 'copy_data', True),
            'src_azs': res_azs
        }
        initial.update(show_filter(plan))
        return initial


class IncrementalCloneView(forms.ModalFormView):
    modal_header = _("Increment Plan")
    form_class = plan_forms.ClonePlan
    form_id = 'incremental_clone_form'
    template_name = 'plans/clone.html'
    success_url = reverse_lazy("horizon:conveyor:plans:index")

    def get_context_data(self, **kwargs):
        plan = getattr(self, 'plan')
        submit_url = 'horizon:conveyor:plans:incremental_clone'
        self.submit_url = reverse(submit_url,
                                  kwargs={'plan_id': plan.plan_id})
        context = super(IncrementalCloneView, self)\
            .get_context_data(**kwargs)

        context['plan_id'] = plan.plan_id
        context['is_original'] = True
        plan_deps_table = plan_tables.PlanDepsTable(
            self.request,
            plan_tables.trans_plan_deps(plan.updated_dependencies),
            plan_id=plan.plan_id,
            plan_type=constants.CLONE
        )
        context['plan_deps_table'] = plan_deps_table.render()

        d3_data = topology.load_d3_data(self.request,
                                        plan.updated_dependencies)
        context['d3_data'] = d3_data
        return context

    def create_incremental_plan(self, plan_id):
        try:
            plan = api.plan_get_brief(self.request, plan_id)
            return api.create_increment_plan(self.request, plan_id,
                                             plan.plan_type)
        except Exception as e:
            LOG.error('Unable to create incremental plan %s. %s', plan_id, e)
            exceptions.handle(self.request,
                              _('Unable to create incremental plan.'),
                              redirect=self.success_url)
        return None

    def get_initial(self):
        increment_plan = self.create_incremental_plan(self.kwargs['plan_id'])
        setattr(self, 'plan', increment_plan)

        return {
            'plan_id': self.kwargs['plan_id'],
            'is_original': True,
        }


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
        d3_data = topology.load_d3_data(request, local_deps)
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
        d3_data = topology.load_d3_data(request, local_deps)
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
        d3_data = topology.load_d3_data(request, global_deps)
        return http.HttpResponse(d3_data,
                                 content_type='application/json')
