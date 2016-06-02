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
from django import http
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse_lazy
from django.views.generic import View

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from conveyordashboard.api import api
from conveyordashboard.plans import forms as plan_forms
from conveyordashboard.plans import resources
from conveyordashboard.plans import tables as plan_tables
from conveyordashboard.plans import tabs as plan_tabs
from conveyordashboard.topology import tables as topology_table
from conveyordashboard.topology import topology

LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = plan_tables.PlansTable
    template_name = 'plans/index.html'
    page_title = _('Plans')

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
                              _('Unable to retrieve plan list.'))
        for plan in plans:
            setattr(plan, "id", plan.plan_id)
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
        context["plan_id"] = self.kwargs['plan_id']
        context["plan"] = plan
        context["url"] = reverse(self.redirect_url)
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


class CreateView(forms.ModalFormView):
    form_class = plan_forms.CreatePlan
    form_id = "plan_topology_form"
    modal_header = _("Plan Topology")
    template_name = 'plans/topology.html'
    context_object_name = 'plan'
    submit_url = reverse_lazy("horizon:conveyor:plans:create")
    success_url = reverse_lazy("horizon:conveyor:plans:index")
    page_title = _("Plan Topology")

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)

        self.set_success_url()

        plan, is_original = self.get_object()

        context['plan'] =  plan
        context['plan_id'] = plan.plan_id

        d3_data = topology.load_plan_d3_data(self.request,
                                             plan,
                                             self.request.GET["type"],
                                             is_original)
        context['d3_data'] = d3_data
        context['is_original'] = is_original

        context['azs'] = self.get_zones()

        try:
            context["type"] = self.request.GET["type"]
        except Exception:
            redirect = CreateView.success_url
            msg = _("Query string does not contain parameter plan type.")
            exceptions.handler(self.request, msg, redirect=redirect)

        return context

    @memoized.memoized_method
    def get_object(self, *args, **kwargs):
        LOG.info("request={}".format(self.request))
        if "ids" in self.request.GET:
            resource = []
            id_list = {}
            try:
                ids = self.request.GET["ids"]
                plan_type = self.request.GET["type"]
                LOG.info("ids=%s, plan_type=%s" % (ids, plan_type))
                for item in ids.split("**"):
                    id_list[item.split("*")[0]] = item.split("*")[1].split(",")
                for key, value in id_list.items():
                    for id in value:
                        resource.append({"type": key, "id": id})
                return api.plan_create(self.request, plan_type, resource), True
            except Exception as e:
                redirect = CreateView.success_url
                msg = _("Query string is not a correct format. error=%s"%str(e))
                exceptions.handle(self.request, msg, redirect=redirect)
                return
        elif "plan_id" in self.request.GET:
            try:
                return (api.plan_get(self.request, self.request.GET["plan_id"]),
                        False)
            except Exception:
                redirect = CreateView.success_url
                msg = _('Unable to retrieve plan details.')
                exceptions.handle(self.request, msg, redirect=redirect)
                return

        redirect = CreateView.success_url
        msg = _('Query string does not contain either plan_id or res ids.')
        exceptions.handle(self.request, msg, redirect=redirect)

    def get_zones(self, *args, **kwargs):
        try:
            zones = api.availability_zone_list(self.request)
            return zones
        except Exception:
            zones = []
            exceptions.handle(self.request,
                              _('Unable to retrieve availability zones.'))

    def set_success_url(self):
        try:
            if "next_url" in self.request.GET:
                CreateView.success_url = self.request.GET["next_url"]
            else:
                CreateView.success_url = self.request.HTTP_REFERER
        except:
            pass

    def get_initial(self):
        initial = super(CreateView, self).get_initial()
        return initial


class ImportView(forms.ModalFormView):
    form_class = plan_forms.ImportPlan
    form_id = "import_plan_form"
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
            plan_id = kwargs["plan_id"]
            plan = api.download_template(request, plan_id)
        except Exception:
            redirect = reverse('horizon:conveyor:plans:index')
            exceptions.handle(request,
                              _('Unable to export plan: %(exc)s'),
                              redirect=redirect)
            return
 
        response = http.HttpResponse(content_type='application/binary')
        response['Content-Disposition'] = ('attachment; filename=%s.plan'
                                           % plan_id)
        template = yaml.dump(yaml.load(json.dumps(plan[1]["template"])))
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


class DestinationView(forms.ModalFormView):
    form_class = plan_forms.Destination
    form_id = "clone_form"
    modal_header = _("Clone")
    template_name = 'plans/destination.html'
    context_object_name = 'plan'
    submit_label = _("Clone")
    submit_url = reverse_lazy("horizon:conveyor:plans:destination")
    success_url = reverse_lazy("horizon:conveyor:plans:index")
    page_title = _("Destination")
    def get_context_data(self, **kwargs):
        context = super(DestinationView, self).get_context_data(**kwargs)
        context["plan_id"] = self.kwargs['plan_id']
        return context

    def get_initial(self):
        initial = super(DestinationView, self).get_initial()
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
            msg = {"msg": "success"}
        except Exception as e:
            msg = {"msg": "err"}
        return http.HttpResponse(json.dumps(msg),
                                 content_type='application/json')


class UpdateView(View):
    @staticmethod
    def post(request, **kwargs):
        plan_id = kwargs["plan_id"]
        POST = request.POST
        LOG.info("Update Plan: Post={}".format(POST))
        plan = api.plan_get(request, plan_id)

        #updated_resources
        i_updated_resources = json.JSONDecoder()\
                                  .decode(POST['updated_resources'])
        updated_resources = plan.updated_resources
        updated_resources.update(i_updated_resources)

        #dependenies
        i_dependencies = json.JSONDecoder().decode(POST["dependencies"])
        dependencies = plan.original_dependencies
        dependencies.update(i_dependencies)

        data = json.JSONDecoder().decode(POST["data"])

        planupdate = resources.PlanUpdate(request,
                                          plan_id,
                                          updated_resources,
                                          dependencies)

        #execute update resource items of plan
        planupdate.execute(data)

        (updated_resources,
         dependencies,
         update_resource) = planupdate.execute_return()

        (i_updated_resources,
         i_dependencies) = resources.update_return_resource(
                                        i_updated_resources,
                                        updated_resources,
                                        i_dependencies,
                                        dependencies)

        d3_data = topology.load_d3_data(request, plan_id, dependencies)

        resp_data = {"d3_data": d3_data,
                     "update_resources":update_resource.values(),
                     "updated_resources": i_updated_resources,
                     "dependencies": i_dependencies}
        return http.HttpResponse(json.dumps(resp_data),
                                 content_type='application/json')


class ResourceDetailJsonView(View):
    @staticmethod
    def post(request, **kwargs):
        POST = request.POST
        plan_id = POST['plan_id']
        is_original = POST['is_original']
        if is_original == "True":
            is_original = True
        elif is_original == "False":
            is_original = False
        else:
            exceptions.handle(
                    request,
                    message=_('Request parameter is not correct.'),
                    ignore=True)

        resource_type = POST['resource_type']
        resource_id = POST['resource_id']
        update_data = json.JSONDecoder().decode(POST["update_data"])
        updated_res = json.JSONDecoder().decode(POST["updated_res"])
        data = resources.ResourceDetailFromPlan(request,
                                                plan_id,
                                                resource_type,
                                                resource_id,
                                                update_data,
                                                updated_res,
                                                is_original).render()
        resp = {"msg": "success",
                "data": data,
                "image": api.get_resource_image(resource_type, 'red')}
        return http.HttpResponse(json.dumps(resp),
                                 content_type='application/json')


class SecgroupRulesView(View):
    @staticmethod
    def get(request, **kwargs):
        sg_id = kwargs["secgroup_id"]
        sg = api.sg_get(request, sg_id)
        rules_table = topology_table.RulesTable(request, sg.rules)
        return http.HttpResponse(rules_table.render(),
                                 content_type='text/html')
