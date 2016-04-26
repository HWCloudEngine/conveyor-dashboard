# Copyright 2013 Kylin OS, Inc
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
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from conveyordashboard.api import api

LOG = logging.getLogger(__name__)


class ImportPlan(forms.SelfHandlingForm):
    plan_help = _("A script or set of commands to be executed after the "
                    "instance has been built (max 16kb).")
    plan_upload = forms.FileField(
        label=_('Plan File'),
        help_text=plan_help,
        required=True)
    def __init__(self, request, *args, **kwargs):
        super(ImportPlan, self).__init__(request, *args, **kwargs)

    def handle(self, request, data):
        try:
            plan_file = request.FILES['plan_upload']
            template = plan_file.read()
            api.create_plan_by_template(request, template)
            messages.success(request,
                             _('Successfully imported plan: %s')
                             % data['plan_upload'].name)
            return True
        except Exception:
            msg = _('Unable to import clone plan.')
            redirect = reverse('horizon:conveyor:plans:index')
            exceptions.handle(request, msg, redirect=redirect)


class CloneDestination(forms.SelfHandlingForm):
    az = forms.ChoiceField(label=_("Target Availability Zone"),
                           required=False)
    host = forms.ChoiceField(label=_("Host"),
                             required=False)

    def __init__(self, request, *args, **kwargs):
        super(CloneDestination, self).__init__(request, *args, **kwargs)
        initial = kwargs.get('initial', {})
        plan_id = initial.get('plan_id')
        self.fields['plan_id'] = forms.CharField(widget=forms.HiddenInput,
                                                     initial=plan_id)
        try:
            zones = api.availability_zone_list(request)
            #api.resource_list(request, "OS::Nova::AvailabilityZone")
            LOG.info("zones={}".format([z.__dict__ for z in zones]))
        except Exception:
            zones = []
            exceptions.handle(request, _('Unable to retrieve availability '
                                         'zones.'))

        zone_list = [(forms.fields.get_dc(zone.zoneName),
                      forms.fields.get_dcname(zone.zoneName))
                      for zone in zones if zone.zoneState['available']]
        zone_list.insert(0, ("", _("Any")))
        zone_list = [(zone.zoneName, zone.zoneName)
                      for zone in zones if zone.zoneState['available']]
        self.fields["az"].choices = dict.fromkeys(zone_list).keys()

    def handle(self, request, data):
        try:
            LOG.info("CloneDestination: data={0}".format(data))
            plan_id = data["plan_id"]
            az = data["az"]
            if az == "": az = None
            api.clone(request, plan_id, az, None)
            msg = _('Successfully Clone plan_id: %s' % data["plan_id"])
            messages.success(request, msg)
            return True
        except:
            msg = _('Failed to clone plan plan_id "%s".') % data['plan_id']
            redirect = reverse('horizon:conveyor:plans:index')
            exceptions.handle(request, msg, redirect=redirect)
