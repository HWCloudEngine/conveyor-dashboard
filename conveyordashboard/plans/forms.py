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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from oslo_log import log as logging

from conveyordashboard.api import api
from conveyordashboard.common import constants
from conveyordashboard.common import utils

LOG = logging.getLogger(__name__)


class CreateForm(forms.SelfHandlingForm):
    plan_name = forms.CharField(
        label=_('Plan Name'),
        max_length=255,
        required=False)
    plan_type = forms.ChoiceField(
        label=_('Plan Type'),
        required=True,
        choices=[(constants.CLONE, _(constants.CLONE)),
                 (constants.MIGRATE, _(constants.MIGRATE))])
    resources = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, request, *args, **kwargs):
        super(CreateForm, self).__init__(request, *args, **kwargs)

    def handle(self, request, data):
        resources = []
        try:
            id_list = {}
            for item in data['resources'].split('**'):
                id_list[item.split('*')[0]] = item.split('*')[1].split(',')
            for key, value in id_list.items():
                for id in value:
                    resources.append({'obj_type': key, 'obj_id': id})
        except Exception as e:
            pass
        try:
            api.plan_create(request, data['plan_type'], resources,
                            plan_name=data['plan_name'])
            messages.info(request, _('Creating plan "%s"') % data['plan_name'])
            return True
        except Exception as e:
            LOG.error("Unable to create plan. %s", e)
            msg = _("Unable to create plan.")
            redirect = reverse('horizon:conveyor:plans:index')
            exceptions.handle(request, msg, redirect=redirect)


class ImportPlan(forms.SelfHandlingForm):
    plan_upload = forms.FileField(
        label=_('Plan File'),
        required=True)

    def __init__(self, request, *args, **kwargs):
        super(ImportPlan, self).__init__(request, *args, **kwargs)

    def handle(self, request, data):
        try:
            plan_file = request.FILES['plan_upload']
            template = plan_file.read()
            api.create_plan_by_template(request, template)
            messages.success(request,
                             _("Successfully imported plan: %s")
                             % data['plan_upload'].name)
            return True
        except Exception:
            msg = _("Unable to import plan.")
            redirect = reverse('horizon:conveyor:plans:index')
            exceptions.handle(request, msg, redirect=redirect)


class Destination(forms.SelfHandlingForm):
    plan_id = forms.CharField(widget=forms.HiddenInput)
    plan_type = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, request, *args, **kwargs):
        super(Destination, self).__init__(request, *args, **kwargs)
        initial = kwargs.get('initial', {})

        src_azs = initial.get('src_azs')
        for src_az in src_azs:
            self.fields[src_az] = forms.CharField(
                widget=forms.HiddenInput(attrs={'md5': utils.md5(src_az)}),
                initial=src_az)

    def handle(self, request, data):
        return True
