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
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from oslo_log import log as logging

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized
from horizon import workflows

from conveyordashboard.api import api
from conveyordashboard.api import models
from conveyordashboard.common import constants
from conveyordashboard.common import tables as common_tables
from conveyordashboard.plans import forms as plan_forms
from conveyordashboard.plans import tables as plan_tables
from conveyordashboard.plans import tabs as plan_tabs
from conveyordashboard.plans import workflows as plan_workflows

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

    return api.plan_create(request, plan_type, resource)


class CreateView(forms.ModalFormView):
    form_class = plan_forms.CreateForm
    form_id = 'create_plan_form'
    template_name = 'plans/create.html'
    modal_header = _("Create Plan")
    submit_url = reverse_lazy("horizon:conveyor:plans:create")
    success_url = reverse_lazy("horizon:conveyor:plans:index")
    page_title = _("Create Plan")
    submit_label = _("Create")

    def get_initial(self):
        return {
            'resources': self.request.GET.get('ids')
        }


# class DestinationView(tables.DataTableView, forms.ModalFormView):
#     table_class = plan_tables.DestinationAZTable
#     form_class = plan_forms.Destination
#     form_id = 'destination_form'
#     template_name = 'plans/destination.html'
#     context_object_name = 'plan'
#     success_url = reverse_lazy("horizon:conveyor:plans:index")
#     submit_label = _("Build Topology")
#
#     def get_data(self):
#         plan_id = self.kwargs['plan_id']
#         res_azs = self.get_plan_res_azs(plan_id)
#         return [models.Resource({'availability_zone': az}) for az in res_azs]
#
#     @memoized.memoized_method
#     def get_plan_res_azs(self, plan_id):
#         try:
#             plan_res_azs = api.list_clone_resources_attribute(
#                 self.request,
#                 plan_id,
#                 'availability_zone')
#             LOG.info('plan_res_azs: %s', plan_res_azs)
#             return plan_res_azs or []
#         except Exception:
#             msg = _(
#                 "Unable to retrieve availability zones for plan resource.")
#             exceptions.handle(self.request, msg)
#
#     def get_context_data(self, **kwargs):
#         plan_id = self.kwargs['plan_id']
#         plan_type = self.request.GET.get('type')
#         if plan_type == constants.CLONE:
#             self.modal_header = self.page_title = _('Clone Destination')
#         else:
#             self.modal_header = self.page_title = _('Migrate Destination')
#
#         submit_url = 'horizon:conveyor:plans:%s' % plan_type
#         self.submit_url = reverse(submit_url,
#                                   kwargs={'plan_id': plan_id})
#
#         context = super(DestinationView,
#                         self).get_context_data(**kwargs)
#         context['form'] = self.get_form()
#         context['plan_type'] = plan_type
#
#         try:
#             availability_zones = api.availability_zone_list(self.request)
#         except Exception:
#             availability_zones = []
#             exceptions.handle(self.request,
#                               _("Unable to retrieve availability zones."))
#         context['availability_zones'] = json.dumps(
#             [az.zoneName for az in availability_zones])
#         return context
#
#     def get_initial(self):
#         plan_id = self.kwargs['plan_id']
#         plan_type = self.request.GET.get('type')
#         if plan_type not in constants.PLAN_TYPE:
#             LOG.error("Invalid plan type %s.", plan_type)
#             exceptions.handle(self.request,
#                               _("Invalid plan type %s.") % plan_type)
#
#         res_azs = self.get_plan_res_azs(plan_id)
#         initial = {
#             'plan_id': plan_id,
#             'plan_type': plan_type,
#             'src_azs': res_azs
#         }
#         return initial
#
#     @memoized.memoized_method
#     def get_form(self, **kwargs):
#         form_class = kwargs.get('form_class', self.get_form_class())
#         return super(DestinationView, self).get_form(form_class)
#
#     def get(self, request, *args, **kwargs):
#         # Table action handling
#         handled = self.construct_tables()
#         if handled:
#             return handled
#         return self.render_to_response(self.get_context_data(**kwargs))
#
#     def post(self, request, *args, **kwargs):
#         form = self.get_form()
#         if form.is_valid():
#             return self.form_valid(form)
#         else:
#             return self.get(request, *args, **kwargs)


class DestinationView(forms.ModalFormView):
    form_class = plan_forms.Destination
    form_id = 'destination_form'
    template_name = 'plans/destination.html'
    context_object_name = 'plan'
    success_url = reverse_lazy("horizon:conveyor:plans:index")

    @memoized.memoized_method
    def get_plan_res_azs(self, plan_id):
        try:
            plan_res_azs = api.list_clone_resources_attribute(
                self.request,
                plan_id,
                'availability_zone')
            return plan_res_azs or []
        except Exception:
            msg = _("Unable to retrieve availability zones for plan resource.")
            exceptions.handle(self.request, msg)

    def get_context_data(self, **kwargs):
        plan_id = self.kwargs['plan_id']
        plan_type = self.request.GET.get('type')
        if plan_type == constants.CLONE:
            self.modal_header = self.page_title = _('Clone Destination')
        else:
            self.modal_header = self.page_title = _('Migrate Destination')
        submit_url = 'horizon:conveyor:plans:clone'
        self.submit_url = reverse(submit_url,
                                  kwargs={'plan_id': plan_id})
        context = super(DestinationView,
                        self).get_context_data(**kwargs)
        context['plan_id'] = plan_id
        context['plan_type'] = plan_type

        res_azs = self.get_plan_res_azs(plan_id)
        LOG.info("@@@Get res_azs: %s", res_azs)
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
        plan_id = self.kwargs['plan_id']
        plan_type = self.request.GET.get('type')
        if plan_type not in constants.PLAN_TYPE:
            LOG.error("Invalid plan type %s.", plan_type)
            exceptions.handle(self.request,
                              _("Invalid plan type %s.") % plan_type)

        res_azs = self.get_plan_res_azs(plan_id)
        initial = {
            'plan_id': plan_id,
            'plan_type': plan_type,
            'src_azs': res_azs
        }
        return initial


class CloneView(workflows.WorkflowView):
    workflow_class = plan_workflows.ClonePlan
    success_url = reverse_lazy("horizon:conveyor:plans:index")

    def get_context_data(self, **kwargs):
        context = super(CloneView, self).get_context_data(**kwargs)

        plan_id = self.kwargs['plan_id']
        context['plan_id'] = plan_id

        return context

    def get_initial(self):
        plan_id = self.kwargs['plan_id']
        return {
            'plan_id': plan_id
        }


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


def display_filter(deps):
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
