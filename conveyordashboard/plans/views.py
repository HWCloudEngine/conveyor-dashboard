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
import logging

from django.core.urlresolvers import reverse
from django.conf import settings
from django import http
from django.template.defaultfilters import slugify
from django.template.defaultfilters import floatformat  # noqa
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse_lazy
from django.utils.datastructures import SortedDict
from django.views.generic import View

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import csvbase
from horizon.utils import memoized

from conveyordashboard.api import api
from conveyordashboard.plans import forms as plan_forms
from conveyordashboard.plans import tables as plan_tables
from conveyordashboard.plans import tabs as plan_tabs

LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = plan_tables.PlanTable
    template_name = 'plans/index.html'
    page_title = _('Plans')

    @memoized.memoized_method
    def get_data(self):
        marker = self.request.GET.get(
            plan_tables.PlanTable._meta.pagination_param, None)
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


class ExportView(View):
    def get(self, request, plan_id=None):
        try:
            plan = api.plan_get(request, plan_id)
        except Exception:
            redirect = reverse('horizon:conveyor:plans:index')
            exceptions.handle(self.request,
                              _('Unable to export plan: %(exc)s'),
                              redirect=redirect)

        response = http.HttpResponse(content_type='application/binary')
        response['Content-Disposition'] = ('attachment; filename=%s.plan'
                                           % slugify(plan_id))
        response.write(str(plan.__dict__))
        response['Content-Length'] = str(len(response.content))
        return response


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


class CloneDestinationView(forms.ModalFormView):
    form_class = plan_forms.CloneDestination
    form_id = "clone_form"
    modal_header = _("Clone")
    template_name = 'plans/clone_destination.html'
    context_object_name = 'plan'
    submit_label = _("Clone")
    submit_url = reverse_lazy("horizon:conveyor:plans:clone")
    success_url = reverse_lazy("horizon:conveyor:plans:index")
    page_title = _("Clone Destination")
    def get_context_data(self, **kwargs):
        context = super(CloneDestinationView, self).get_context_data(**kwargs)
        context["plan_id"] = self.kwargs['plan_id']
        return context

    def get_initial(self):
        initial = super(CloneDestinationView, self).get_initial()
        initial.update({'plan_id': self.kwargs['plan_id']})
        return initial
