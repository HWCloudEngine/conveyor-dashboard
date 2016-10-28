# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

import json
import logging
import yaml

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django import http
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from oslo_utils import strutils

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from conveyordashboard.api import api
from conveyordashboard.api import models
from conveyordashboard.common import constants
from conveyordashboard.plans import forms as plan_forms
from conveyordashboard.plans import resources
from conveyordashboard.plans import tables as plan_tables
from conveyordashboard.plans import tabs as plan_tabs
from conveyordashboard.topology import tables as topology_tables
from conveyordashboard.topology import topology

LOG = logging.getLogger(__name__)


def trans_plan_deps(plan_deps):
    deps = []
    LOG.info("plan_deps: %s", plan_deps)
    for dep in plan_deps.values():
        deps.append(models.Resource(dep))
    return deps


class IndexView(tables.DataTableView):
    table_class = plan_tables.PlansTable
    template_name = 'plans/index.html'
    page_title = _("Plans")

    @memoized.memoized_method
    def get_data(self):
        marker = self.request.GET.get(
            plan_tables.PlansTable._meta.pagination_param, None)
        search_opts = self.get_filters({'marker': marker, 'paginate': True})

        try:
            plans = api.plan_list(self.request, search_opts=search_opts)
            tenant_id = self.request.user.tenant_id
            plans = [plan for plan in plans if plan.project_id == tenant_id]
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
    template_name = 'plans/detail.html'
    redirect_url = 'horizon:conveyor:plans:index'
    page_title = _("Plan Details: {{ plan_id }}")

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        plan = self.get_data()
        context['plan_id'] = self.kwargs['plan_id']
        context['plan'] = plan
        context['url'] = reverse(self.redirect_url)
        return context

    @memoized.memoized_method
    def get_data(self):
        plan_id = self.kwargs['plan_id']
        try:
            plan = api.plan_get(self.request, plan_id)
        except Exception:
            exceptions.handle(self.request, _("Unable to retrieve plan."))
        return plan

    def get_tabs(self, request, *args, **kwargs):
        plan = self.get_data()
        return self.tab_group_class(request, plan=plan, **kwargs)


class CloneView(forms.ModalFormView):
    form_class = plan_forms.ClonePlan
    form_id = 'plan_topology_form'
    modal_header = _("Plan Topology")
    template_name = 'plans/clone.html'
    context_object_name = 'plan'
    submit_url = reverse_lazy("horizon:conveyor:plans:clone")
    success_url = reverse_lazy("horizon:conveyor:plans:index")
    page_title = _("Plan Topology")

    def get_context_data(self, **kwargs):
        context = super(CloneView, self).get_context_data(**kwargs)

        plan, is_original = self.get_object()

        context['type'] = constants.CLONE
        context['plan'] = plan
        context['plan_id'] = plan.plan_id
        CloneView.modal_header = 'Plan Topology ' + plan.plan_id

        plan_deps_table = topology_tables.PlanDepsTable(
            self.request,
            trans_plan_deps(plan.original_dependencies),
            plan_id=plan.plan_id,
            plan_type=constants.CLONE)
        context['plan_deps_table'] = plan_deps_table.render()

        d3_data = topology.load_plan_d3_data(self.request,
                                             plan,
                                             constants.CLONE,
                                             is_original)
        context['d3_data'] = d3_data
        context['is_original'] = is_original
        context['azs'] = self.get_zones()

        return context

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        if 'ids' in self.request.GET:
            resource = []
            id_list = {}
            try:
                ids = self.request.GET['ids']
                for item in ids.split('**'):
                    id_list[item.split('*')[0]] = item.split('*')[1].split(',')
                for key, value in id_list.items():
                    for id in value:
                        resource.append({'type': key, 'id': id})

                return api.plan_create(self.request,
                                       constants.CLONE,
                                       resource), True
            except Exception:
                msg = _("Query string is not a correct format.")
                exceptions.handle(self.request, msg)
                return
        elif 'plan_id' in self.request.GET:
            try:
                return (api.plan_get(self.request,
                                     self.request.GET['plan_id']),
                        False)
            except Exception:
                msg = _("Unable to retrieve plan details.")
                exceptions.handle(self.request, msg)
                return

        msg = _("Query string does not contain either plan_id or res ids.")
        exceptions.handle(self.request, msg)

    def get_zones(self, *args, **kwargs):
        try:
            zones = api.availability_zone_list(self.request)
            return zones
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve availability zones."))

    def get_initial(self):
        initial = super(CloneView, self).get_initial()
        return initial


class MigrateView(forms.ModalFormView):
    form_class = plan_forms.MigratePlan
    form_id = 'plan_migrate_form'
    modal_header = _("Migrate Plan")
    template_name = 'plans/migrate.html'
    context_object_name = 'plan'
    submit_url = reverse_lazy("horizon:conveyor:plans:migrate")
    success_url = reverse_lazy("horizon:conveyor:plans:index")

    def get_context_data(self, **kwargs):
        context = super(MigrateView, self).get_context_data(**kwargs)

        plan, is_original = self.get_object()

        context['plan_id'] = plan.plan_id
        context['type'] = constants.MIGRATE
        MigrateView.modal_header = 'Migrate Plan ' + plan.plan_id

        plan_deps_table = topology_tables.PlanDepsTable(
            self.request,
            trans_plan_deps(plan.original_dependencies),
            plan_id=plan.plan_id,
            plan_type=constants.MIGRATE)
        context['plan_deps_table'] = plan_deps_table.render()

        d3_data = topology.load_plan_d3_data(self.request,
                                             plan,
                                             constants.MIGRATE,
                                             is_original)
        context['d3_data'] = d3_data
        context['is_original'] = is_original
        # az_form = plan_forms.Destination(self.request,
        #                                  initial={'plan_id': plan.plan_id})
        context['azs'] = self.get_zones()
        # context['az_form'] = az_form.as_table()

        return context

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        if 'ids' in self.request.GET:
            resource = []
            id_list = {}
            try:
                ids = self.request.GET['ids']
                for item in ids.split('**'):
                    id_list[item.split('*')[0]] = item.split('*')[1].split(',')
                for key, value in id_list.items():
                    for id in value:
                        resource.append({'type': key, 'id': id})

                return (api.plan_create(self.request,
                                        constants.MIGRATE,
                                        resource),
                        True)
            except Exception:
                msg = _("Query string is not a correct format.")
                exceptions.handle(self.request, msg)
                return
        elif 'plan_id' in self.request.GET:
            try:
                return (api.plan_get(self.request,
                                     self.request.GET['plan_id']),
                        False)
            except Exception:
                msg = _("Unable to retrieve plan details.")
                exceptions.handle(self.request, msg)
                return

        msg = _("Query string does not contain either plan_id or res ids.")
        exceptions.handle(self.request, msg)

    def get_zones(self, *args, **kwargs):
        try:
            zones = api.availability_zone_list(self.request)
            return zones
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve availability zones."))

    def get_initial(self):
        initial = super(MigrateView, self).get_initial()
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
    page_title = _("Modify")

    def get_context_data(self, **kwargs):
        context = super(ModifyView, self).get_context_data(**kwargs)
        context['plan_id'] = self.kwargs['plan_id']

        plan = self.get_object(**self.kwargs)

        context['type'] = 'clone'
        plan_deps_table = topology_tables.PlanDepsTable(
            self.request,
            trans_plan_deps(plan.updated_dependencies),
            plan_id=plan.plan_id,
            plan_type=constants.CLONE
        )
        context['plan_deps_table'] = plan_deps_table.render()

        d3_data = topology.load_d3_data(self.request, plan.plan_id,
                                        plan.updated_dependencies)
        # d3_data = topology.load_plan_d3_data(self.request,
        #                                      plan,
        #                                      'clone')
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
        response['Content-Disposition'] = ('attachment; filename=%s.plan'
                                           % plan_id)
        template = yaml.dump(yaml.load(json.dumps(plan[1]['template'])))
        response.write(template)
        response['Content-Length'] = str(len(response.content))
        return response


class CreateTriggerView(forms.ModalFormView):
    form_class = plan_forms.ImportPlan
    template_name = 'plans/create_trigger.html'
    context_object_name = 'plan'
    success_url = reverse_lazy("horizon:conveyor:plans:index")
    page_title = _("Import Clone Plan")

    def get_context_data(self, **kwargs):
        context = super(CreateTriggerView, self).get_context_data(**kwargs)
        return context

    def get_initial(self):
        initial = super(CreateTriggerView, self).get_initial()
        return initial


class MigrateDestinationView(forms.ModalFormView):
    form_class = plan_forms.MigrateDestination
    form_id = 'migrate_destination_form'
    modal_header = _("Migrate Destination")
    template_name = 'plans/migrate_destination.html'
    context_object_name = 'plan'
    submit_label = _("Migrate")
    submit_url = reverse_lazy("horizon:conveyor:plans:migrate_destination")
    success_url = reverse_lazy("horizon:conveyor:plans:index")
    page_title = _("Migrate Destination")

    def get_context_data(self, **kwargs):
        context = super(MigrateDestinationView,
                        self).get_context_data(**kwargs)
        return context

    def get_initial(self):
        initial = super(MigrateDestinationView, self).get_initial()
        initial.update({'plan_id': self.kwargs['plan_id']})
        return initial


class CancelView(View):
    @staticmethod
    def post(request, **kwargs):
        try:
            plan_id = kwargs['plan_id']
            api.plan_delete(request, plan_id)
            LOG.info("Cancel plan {0} and delete it "
                     "successfully.".format(plan_id))
            msg = {'msg': 'success'}
        except Exception:
            msg = {'msg': 'err'}
        return http.HttpResponse(json.dumps(msg),
                                 content_type='application/json')


class UpdateView(View):
    @staticmethod
    def post(request, **kwargs):
        plan_id = kwargs['plan_id']
        POST = request.POST
        LOG.info("Update Plan: Post={}".format(POST))
        plan = api.plan_get(request, plan_id)

        # Updated_resources
        i_updated_resources = json.JSONDecoder()\
                                  .decode(POST['updated_resources'])
        updated_resources = plan.updated_resources
        updated_resources.update(i_updated_resources)

        # Dependenies
        i_dependencies = json.JSONDecoder().decode(POST['dependencies'])
        dependencies = plan.original_dependencies
        dependencies.update(i_dependencies)

        data = json.JSONDecoder().decode(POST['data'])

        # Update res
        update_res = json.JSONDecoder().decode(POST['update_res'])
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
        deps = dict([(key, value) for key, value in dependencies.items() if value.get(constants.RES_ACTION_KEY, '') != constants.ACTION_DELETE])

        res_deps = topology_tables.PlanDepsTable(
            request,
            trans_plan_deps(deps),
            plan_id=plan.plan_id,
            plan_type=constants.CLONE).render()

        d3_data = topology.load_d3_data(request, plan_id, deps)

        resp_data = {'d3_data': d3_data,
                     'res_deps': res_deps,
                     'update_resources': ret_res.values(),
                     'updated_resources': i_updated_resources,
                     'dependencies': i_dependencies}
        return http.HttpResponse(json.dumps(resp_data),
                                 content_type='application/json')

        (updated_resources,
         dependencies,
         update_resource) = planupdate.execute_return()

        LOG.info(
            "i_updated_resources: %(1)s\n\ni_dependencies: %(2)s\n\n",
            {'1': i_updated_resources, '2': i_dependencies})
        LOG.info("updated_resources: %(1)s\n\ndependencies: %(2)s\n\nupdate_resource: %(3)s\n\n", {'1': updated_resources, '2': dependencies, '3': update_resource})
        (i_updated_resources,
         i_dependencies) = resources.update_return_resource(
            i_updated_resources,
            updated_resources,
            i_dependencies,
            dependencies)
        LOG.info(
            "i_updated_resources: %(1)s\n\ni_dependencies: %(2)s\n\n",
            {'1': i_updated_resources, '2': i_dependencies})

        deps = dict([(key, value) for key, value in dependencies.items() if value.get(constants.RES_ACTION_KEY, '') != constants.ACTION_DELETE])
        d3_data = topology.load_d3_data(request, plan_id, deps)

        resp_data = {'d3_data': d3_data,
                     'update_resources': update_resource.values(),
                     'updated_resources': i_updated_resources,
                     'dependencies': i_dependencies}
        return http.HttpResponse(json.dumps(resp_data),
                                 content_type='application/json')


class ResourceDetailJsonView(View):
    @staticmethod
    def post(request, **kwargs):
        POST = request.POST
        # LOG.info("res_detail request.POST: %s", POST)
        plan_id = POST['plan_id']
        is_original = strutils.bool_from_string(POST.get('is_original', False))

        resource_type = POST['resource_type']
        resource_id = POST['resource_id']
        update_data = json.JSONDecoder().decode(POST['update_data'])
        updated_res = json.JSONDecoder().decode(POST['updated_res'])
        data = resources.ResourceDetailFromPlan(
            request, plan_id, resource_type, resource_id,
            update_data, updated_res, is_original).render()
        resp = {'msg': 'success',
                'data': data,
                'image': api.get_resource_image(resource_type, 'red')}
        return http.HttpResponse(json.dumps(resp),
                                 content_type='application/json')
