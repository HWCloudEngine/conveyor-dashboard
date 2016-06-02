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

import base64
import json
import logging
import six

from oslo_utils import encodeutils

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
            LOG.info("Plan template\n{0}".format(template))
            api.create_plan_by_template(request, template)
            messages.success(request,
                             _('Successfully imported plan: %s')
                             % data['plan_upload'].name)
            return True
        except Exception:
            msg = _('Unable to import clone plan.')
            redirect = reverse('horizon:conveyor:plans:index')
            exceptions.handle(request, msg, redirect=redirect)


def preprocess_update_resources(update_resources):
    for resource in update_resources:
        if resource["type"] == "OS::Nova::Server":
            if resource.get("user_data", None):
                user_data = resource["user_data"]
                if six.PY3:
                    try:
                        user_data = user_data.encode("utf-8")
                    except AttributeError:
                        pass
                else:
                    try:
                        user_data = encodeutils.safe_encode(user_data)
                    except UnicodeDecodeError:
                        pass
                user_data = base64.b64encode(user_data).decode('utf-8')
                resource["user_data"] = user_data


def clone_plan(request, action_type):
    POST = request.POST
    plan_id = POST["plan_id"]
    update_resources = json.JSONDecoder().decode(POST["update_resource"])
    preprocess_update_resources(update_resources)
    LOG.info("Get update resources for clone plan. "
             "update_resources={}".format(update_resources))
    az = POST.get("availability_zone", None)

    if action_type == "clone":
        api.clone(request, plan_id, az, update_resources)
    elif action_type == "save":
        api.export_clone_template(request, plan_id, update_resources)
    else:
        api.plan_delete(request, plan_id)
    msg = ("%s plan %s successfully." % (action_type.title(), plan_id))
    return msg


def migrate_plan(request, action_type):
    POST = request.POST
    plan_id = POST["plan_id"]
    az = POST.get("availability_zone", None)

    if action_type == "migrate":
        api.migrate(request, plan_id, az)
    elif action_type == "save":
        api.export_migrate_template(request, plan_id)
    else:
        api.plan_delete(request, plan_id)
    msg = ("%s plan %s successfully." % (action_type.title(), plan_id))
    return msg


class CreatePlan(forms.SelfHandlingForm):
    def __init__(self, request, *args, **kwargs):
        super(CreatePlan, self).__init__(request, *args, **kwargs)

    def handle(self, request, data):
        try:
            POST = request.POST
            plan_type = POST["plan_type"]
            action_type = POST["action_type"]
            if plan_type not in ["clone", "migrate"]:
                LOG.error("Plan type only support clone or migrate. "
                          "while plan_type here is %s" % plan_type)
                raise Exception
            if plan_type == "clone":
                if action_type not in ["clone", "save", "cancel"]:
                    LOG.error("Action type only support clone, save or cancel "
                              "for plan_type <%s>. while action_type "
                              "here is %s" % (plan_type, action_type))
                    raise Exception
                msg = clone_plan(request, action_type)
            else:
                if action_type not in ["migrate", "save", "cancel"]:
                    LOG.error("Action type only support clone, migrate or "
                              "cancel for plan_type <%s>. while action_type "
                              "here is %s" % (plan_type, action_type))
                    raise Exception
                msg = migrate_plan(request, action_type)
            messages.success(request, msg)
            return True
        except Exception:
            msg = _('Some error occurs when processing plan host.')
            redirect = reverse('horizon:conveyor:instances:index')
            exceptions.handle(request, msg, redirect=redirect)


class Destination(forms.SelfHandlingForm):
    az = forms.ChoiceField(label=_("Target Availability Zone"),
                           required=False)
    host = forms.ChoiceField(label=_("Host"),
                             required=False)

    def __init__(self, request, *args, **kwargs):
        super(Destination, self).__init__(request, *args, **kwargs)
        initial = kwargs.get('initial', {})
        plan_id = initial.get('plan_id')
        self.fields['plan_id'] = forms.CharField(widget=forms.HiddenInput,
                                                     initial=plan_id)

        try:
            zones = api.availability_zone_list(request)
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
