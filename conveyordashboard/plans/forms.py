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

import base64
import json
import six

from oslo_utils import encodeutils
from oslo_utils import strutils

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from oslo_log import log as logging

from conveyordashboard.api import api
from conveyordashboard.common import constants

TAG_RES_TYPE = constants.TAG_RES_TYPE

LOG = logging.getLogger(__name__)


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


def preprocess_update_resources(update_resources):
    for res in update_resources:
        if res.get(constants.RES_ACTION_KEY, '') in (constants.ACTION_DELETE,
                                                     constants.ACTION_ADD):
            update_resources.remove(res)
        else:
            res[constants.RES_ACTION_KEY] = constants.ACTION_EDIT

    for res in update_resources:
        if res[TAG_RES_TYPE] == constants.NOVA_SERVER:
            if res.get('user_data', None):
                user_data = res['user_data']
                if six.PY3:
                    try:
                        user_data = user_data.encode('utf-8')
                    except AttributeError:
                        pass
                else:
                    try:
                        user_data = encodeutils.safe_encode(user_data)
                    except UnicodeDecodeError:
                        pass
                user_data = base64.b64encode(user_data).decode('utf-8')
                res['user_data'] = user_data
        elif res[TAG_RES_TYPE] == constants.NEUTRON_SUBNET:
            res.pop('from_network_id', None)
            if 'no_gateway' in res:
                if res['no_gateway']:
                    res['gateway_ip'] = None
                res.pop('no_gateway')

            if 'allocation_pools' in res \
                    and isinstance(res['allocation_pools'], six.string_types):
                pools = [dict(zip(['start', 'end'], pool.strip().split(',')))
                         for pool in res['allocation_pools'].split('\n')
                         if pool.strip()]
                res['allocation_pools'] = pools
            if 'host_routes' in res and isinstance(res['host_routes'],
                                                   six.string_types):
                routes = [dict(zip(['destination', 'nexthop'],
                                   route.strip().split(',')))
                          for route in res['host_routes'].split('\n')
                          if route.strip()]
                res['host_routes'] = routes
            if 'dns_nameservers' in res and isinstance(res['dns_nameservers'],
                                                       six.string_types):
                nameservers = [ns.strip()
                               for ns in res['dns_nameservers'].split('\n')
                               if ns.strip()]
                res['dns_nameserver'] = nameservers
        elif res[TAG_RES_TYPE] == constants.NEUTRON_NET:
            if 'value_specs' in res:
                val_specs = res['value_specs']
                specs = {}
                if 'router_external' in val_specs:
                    specs['router:external'] = strutils.bool_from_string(
                        val_specs.pop('router_external'))
                if 'segmentation_id' in val_specs:
                    specs['provider:segmentation_id'] \
                        = int(val_specs.pop('segmentation_id'))
                if 'physical_network' in val_specs:
                    specs['provider:physical_network'] \
                        = val_specs.pop('physical_network')
                if 'network_type' in val_specs:
                    specs['provider:network_type'] \
                        = val_specs.pop('network_type')
                res['value_specs'] = specs
            if 'admin_state_up' in res:
                res['admin_state_up'] \
                    = strutils.bool_from_string(res['admin_state_up'])
        elif res[TAG_RES_TYPE] == constants.NEUTRON_SECGROUP:
            if 'rules' in res:
                rules = res['rules']
                if isinstance(rules, six.string_types):
                    rules = json.JSONDecoder().decode(rules)
                for r in rules:
                    r.pop('id', None)
                res['rules'] = rules


def update_plan_resource(request, plan_id, resources):
    preprocess_update_resources(resources)
    if len(resources) > 0:
        LOG.info("Update plan %(plan)s with resources %(resources)s",
                 {'plan': plan_id, 'resources': resources})
        api.update_plan_resource(request, plan_id, resources)


class Destination(forms.SelfHandlingForm):
    plan_id = forms.CharField(widget=forms.HiddenInput)
    plan_type = forms.CharField(widget=forms.HiddenInput)
    az = forms.ChoiceField(label=_("Target Availability Zone"),
                           required=True)
    sys_clone = forms.BooleanField(label=_("Clone System Volume"),
                                   required=False)
    copy_data = forms.BooleanField(label=_("Copy Volume Data"),
                                   required=False)

    def __init__(self, request, *args, **kwargs):
        super(Destination, self).__init__(request, *args, **kwargs)
        initial = kwargs.get('initial', {})
        plan_type = initial.get('plan_type')
        if plan_type == constants.CLONE:
            self.fields['resources'] = forms.CharField(
                widget=forms.HiddenInput, initial='[]')

        try:
            zones = api.availability_zone_list(request)
        except Exception:
            zones = []
            exceptions.handle(request,
                              _("Unable to retrieve availability zones."))

        zone_list = [(zone.zoneName, zone.zoneName)
                     for zone in zones if zone.zoneState['available']]

        self.fields["az"].choices = dict.fromkeys(zone_list).keys()

    def handle(self, request, data):
        plan_id = data['plan_id']
        plan_type = data['plan_type']
        zone_name = data['az']

        if plan_type == constants.CLONE:
            try:
                resources = json.loads(data['resources'])
                update_plan_resource(request, plan_id, resources)

                api.export_template_and_clone(request, plan_id, zone_name,
                                              sys_clone=data['sys_clone'],
                                              copy_data=data['copy_data'])
                messages.success(
                    request,
                    _('Execute clone plan %s successfully.') % plan_id)
                return True
            except Exception as e:
                LOG.error("Execute clone plan %(plan_id)s failed. %(error)s",
                          {'plan_id': plan_id, 'error': e})
                redirect = reverse('horizon:conveyor:plans:index')
                exceptions.handle(request,
                                  _("Execute clone plan %s failed.") % plan_id,
                                  redirect=redirect)
        elif plan_type == constants.MIGRATE:
            try:
                api.migrate(request, plan_id, zone_name)
                messages.success(
                    request,
                    _('Execute migrate plan %s successfully.') % plan_id)
                return True
            except Exception as e:
                LOG.error("Execute migrate plan %(plan_id)s failed. %(error)s",
                          {'plan_id': plan_id, 'error': e})
                redirect = reverse('horizon:conveyor:plans:index')
                exceptions.handle(
                    request,
                    _("Execute migrate plan %s failed.") % plan_id,
                    redirect=redirect)
        else:
            msg = _("Unsupported plan type.")
            redirect = reverse('horizon:conveyor:plan:index')
            exceptions.handle(request, msg, redirect=redirect)


class ClonePlan(forms.SelfHandlingForm):
    plan_id = forms.CharField(widget=forms.HiddenInput)
    is_original = forms.CharField(widget=forms.HiddenInput)
    update_resource = forms.CharField(widget=forms.HiddenInput,
                                      initial='[]')
    updated_resources = forms.CharField(widget=forms.HiddenInput,
                                        initial='{}')
    dependencies = forms.CharField(widget=forms.HiddenInput,
                                   initial='{}')

    def handle(self, request, data):
        return True


class MigratePlan(forms.SelfHandlingForm):
    plan_id = forms.CharField(widget=forms.HiddenInput)
    is_original = forms.CharField(widget=forms.HiddenInput)

    def handle(self, request, data):
        return True


class SavePlan(forms.SelfHandlingForm):
    plan_id = forms.CharField(widget=forms.HiddenInput)
    sys_clone = forms.BooleanField(label=_("Clone System Volume"),
                                   required=False)
    copy_data = forms.BooleanField(label=_("Copy Volume Data"),
                                   required=False,
                                   initial=True)
    resources = forms.CharField(widget=forms.HiddenInput,
                                initial='[]')

    def handle(self, request, data):
        LOG.info("Save plan with data: %s", data)
        plan_id = data['plan_id']
        try:
            resources = json.loads(data['resources'])
            update_plan_resource(request, plan_id, resources)
            api.export_clone_template(request, plan_id,
                                      sys_clone=data['sys_clone'],
                                      copy_data=data['copy_data'])
            msg = ("Save plan %s successfully." % plan_id)
            messages.success(request, msg)
            return True
        except Exception as e:
            LOG.error("Save plan %(plan_id)s failed with data %(data)s. "
                      "%(error)s",
                      {'plan_id': plan_id, 'data': data, 'error': e})
            redirect = reverse('horizon:conveyor:plans:index')
            exceptions.handle(request,
                              _("Save plan %s failed.") % plan_id,
                              redirect=redirect)


class ModifyPlan(forms.SelfHandlingForm):
    def __init__(self, request, *args, **kwargs):
        super(ModifyPlan, self).__init__(request, *args, **kwargs)
        initial = kwargs.get('initial', {})
        plan_id = initial.get('plan_id')
        self.fields['plan_id'] = forms.CharField(widget=forms.HiddenInput,
                                                 initial=plan_id)
        self.fields['update_resource'] = forms.CharField(
            widget=forms.HiddenInput, initial=[])
        self.fields['updated_resources'] = forms.CharField(
            widget=forms.HiddenInput, initial={})
        self.fields['dependencies'] = forms.CharField(
            widget=forms.HiddenInput, initial={})

    def handle(self, request, data):
        plan_id = data['plan_id']
        try:
            resources = json.loads(data['update_resource'])
            update_plan_resource(request, plan_id, resources)
            msg = ("Update plan %s successfully." % plan_id)
            messages.success(request, msg)
            return True
        except Exception as e:
            LOG.error("Update plan %(plan_id) failed. %(error)s",
                      {'plan_id': plan_id, 'error': e})
            redirect = reverse('horizon:conveyor:plans:index')
            exceptions.handle(request,
                              _('Update plan %s failed') % plan_id,
                              redirect=redirect)
