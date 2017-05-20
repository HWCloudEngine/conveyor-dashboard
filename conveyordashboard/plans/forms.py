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
import copy
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
                res['dns_nameservers'] = nameservers
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

        if not initial.get('show_az'):
            del self.fields['az']
        else:
            try:
                zones = api.availability_zone_list(request)
            except Exception:
                zones = []
                exceptions.handle(request,
                                  _("Unable to retrieve availability zones."))

            zone_list = [(zone.zoneName, zone.zoneName)
                         for zone in zones if zone.zoneState['available']]

            self.fields["az"].choices = dict.fromkeys(zone_list).keys()
        if not initial.get('show_sys_clone'):
            del self.fields['sys_clone']
        if not initial.get('show_copy_data'):
            del self.fields['copy_data']

    def handle(self, request, data):
        plan_id = data['plan_id']
        plan_type = data['plan_type']
        zone_name = data.get('az', None)

        if plan_type == constants.CLONE:
            try:
                resources = json.loads(data['resources'])
                preprocess_update_resources(resources)

                kwargs = {}
                if 'sys_clone' in data:
                    kwargs['sys_clone'] = data['sys_clone']
                if 'copy_data' in data:
                    kwargs['copy_data'] = data['copy_data']

                api.export_template_and_clone(request, plan_id, zone_name,
                                              resources=resources,
                                              **kwargs)
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

    def __init__(self, request, *args, **kwargs):
        super(SavePlan, self).__init__(request, *args, **kwargs)
        initial = kwargs.get('initial', {})

        if not initial.get('show_sys_clone'):
            del self.fields['sys_clone']
        if not initial.get('show_copy_data'):
            del self.fields['copy_data']

    def handle(self, request, data):
        LOG.info("Save plan with data: %s", data)
        plan_id = data['plan_id']
        try:
            resources = json.loads(data['resources'])
            update_plan_resource(request, plan_id, resources)
            kwargs = {}
            if 'sys_clone' in data:
                kwargs['sys_clone'] = data['sys_clone']
            if'copy_data' in data:
                kwargs['copy_data'] = data['copy_data']
            api.export_clone_template(request, plan_id, **kwargs)
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


def rebuild_dependencies(dependencies):
    """Add reverse dependencies to original dependencies.

    :param dependencies: Original dependencies.
    """
    for res_id, item in dependencies.items():
        if item['dependencies']:
            for d in item['dependencies']:
                if d not in dependencies:
                    LOG.info('%s not in %s', d, dependencies)
                    continue
                if res_id not in dependencies[d]['dependencies']:
                    dependencies[d]['dependencies'].append(res_id)


def search_dependent_items(dependencies,
                           res_ids,
                           search_res_type,
                           excepts=None):
    """Search dependent item.

    :param dependencies:    dependencies used to search.
    :param res_ids:         list of resource id in heat template.
    :param search_res_type: destination resource type that needed to be search.
                            like: server
    :param excepts:         list of resource id. The search result should not
                            contain them.
    :return:                The list of id matched to search_res_type.
    """
    if not excepts:
        excepts = []

    searched_ids = []

    dep_pro = 'dependencies'
    for res_id in res_ids:
        if 'searched' in dependencies[res_id]:
            continue
        for dep_res_id in dependencies[res_id][dep_pro]:
            dependencies[res_id]['searched'] = True
            if search_res_type == dep_res_id.split("_")[0]:
                dependencies[res_id]['searched'] = True
                searched_ids.append(dep_res_id)
            else:
                searched_ids.extend(search_dependent_items(dependencies,
                                                           [dep_res_id],
                                                           search_res_type,
                                                           excepts=excepts))
    for e in excepts:
        if e in searched_ids:
            searched_ids.remove(e)

    return searched_ids

# Edit plan resources
# OS::Nova


class EditResource(forms.SelfHandlingForm):
    plan_id = forms.CharField(widget=forms.HiddenInput())
    res_id = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, request, *args, **kwargs):
        super(EditResource, self).__init__(request, *args, **kwargs)
        self.initial = kwargs.get('initial', {})
        self.plan_id = self.initial.get('plan_id')
        self.res_id = self.initial.get('res_id')
        self.detail = self.initial.get('detail', {})
        self.properties = self.detail.get('properties', {})
        self.parameters = self.detail.get('parameters', {})
        self.extra_properties = self.detail.get('extra_properties', {})


class EditInstance(EditResource):

    def __init__(self, request, *args, **kwargs):
        super(EditInstance, self).__init__(request, *args, **kwargs)

        self.fields['name'] = forms.CharField(
            label='Name',
            widget=forms.TextInput(attrs={'readonly': 'readonly'}),
            initial=self.properties.get('name', ''),
            required=False)
        self.fields['availability_zone'] = forms.CharField(
            label='Availability Zone',
            widget=forms.TextInput(attrs={'readonly': 'readonly'}),
            initial=self.properties.get('availability_zone', ''),
            required=False)
        user_data = self.properties.get('user_data', '')
        if user_data:
            user_data = base64.b64decode(user_data).encode('utf-8')
        self.fields['user_data'] = forms.CharField(
            label='User Data',
            widget=forms.Textarea(attrs={'rows': 4, 'data-ori': user_data}),
            initial=user_data,
            required=False)
        metadata = self.properties.get('metadata', {})
        self.fields['metadata'] = forms.CharField(
            label='Metadata',
            widget=forms.Textarea(attrs={'rows': 4}),
            initial='\n'.join(['%s=%s' % (k, v) for k, v in metadata.items()]),
            required=False)

    def handle(self, request, data):
        return True


class EditKeyPair(EditResource):
    keypairs = forms.ChoiceField(label=_("Key Pair"),
                                 required=False)

    def __init__(self, request, *args, **kwargs):
        super(EditKeyPair, self).__init__(request, *args, **kwargs)

        keypairs = api.resource_list(self.request, constants.NOVA_KEYPAIR)
        self.fields['keypairs'].choices = [(k.name, k.name) for k in keypairs]

    def handle(self, request, data):
        return True


class EditFlavor(EditResource):
    def __init__(self, request, *args, **kwargs):
        super(EditFlavor, self).__init__(request, *args, **kwargs)

        self.fields['ram'] = forms.CharField(
            label='RAM',
            widget=forms.TextInput(attrs={'readonly': 'readonly'}),
            initial=self.properties.get('ram', ''),
            required=False)
        self.fields['vcpus'] = forms.CharField(
            label='VCPUs',
            widget=forms.TextInput(attrs={'readonly': 'readonly'}),
            initial=self.properties.get('vcpus', ''),
            required=False)
        self.fields['disk'] = forms.CharField(
            label='Disk',
            widget=forms.TextInput(attrs={'readonly': 'readonly'}),
            initial=self.properties.get('disk', ''),
            required=False)

    def handle(self, request, data):
        return True


# OS::Volume

class EditVolume(EditResource):

    def __init__(self, request, *args, **kwargs):
        super(EditVolume, self).__init__(request, *args, **kwargs)

        name = self.properties.get('name', '')
        self.fields['name'] = forms.CharField(
            label=_("Name"),
            widget=forms.TextInput(attrs={'data-ori': name}),
            initial=name,
            required=False)
        size = int(self.properties.get('size'))
        self.fields['size'] = forms.IntegerField(
            label=_("Size (GiB)"),
            min_value=size,
            initial=size,
            widget=forms.NumberInput(
                attrs={'data-ori': self.detail.get('id')}))
        metadata = self.properties.get('metadata', {})
        self.fields['metadata'] = forms.CharField(
            label=_("Metadata"),
            widget=forms.Textarea(attrs={'rows': 4}),
            initial='\n'.join(['%s=%s' % (k, v) for k, v in metadata.items()]),
            required=False)
        self.fields['copy_data'] = forms.BooleanField(
            label=_("Copy Volume Data"),
            initial=self.properties.get('copy_data', True),
            required=False)

        self._other_volumes()

    def _other_volumes(self):
        plan = api.plan_get(self.request, self.plan_id)
        dependencies = plan.updated_dependencies
        updated_res = plan.updated_resources
        rebuild_dependencies(dependencies)
        dep_servers = search_dependent_items(dependencies,
                                             [self.res_id],
                                             'server')

        if not len(dep_servers):
            return

        dep_volumes = search_dependent_items(copy.deepcopy(dependencies),
                                             dep_servers,
                                             'volume',
                                             excepts=[self.res_id])
        volumes = api.resource_list(self.request, constants.CINDER_VOLUME)
        volumes = dict([(s.id, s) for s in volumes])
        for dep_volume in dep_volumes:
            if updated_res[dep_volume]['id'] in volumes:
                del volumes[updated_res[dep_volume]['id']]
        self.fields['other'] = forms.BooleanField(
            label=_("Select From Other Volumes"),
            widget=forms.CheckboxInput(attrs={
                'class': 'switchable',
                'data-slug': 'volumes',
                'data-hide-on-checked': 'false'
            }),
            initial=False,
            required=False)
        self.fields['volumes'] = forms.ChoiceField(
            label=_("Volumes"),
            widget=forms.Select(attrs={
                'data-ori': self.detail.get('id'),
                'class': 'switched',
                'data-switch-on': 'volumes',
                'data-source-manual': _("Volumes")
            }),
            initial=self.detail.get('id'),
            choices=[(vol.id, '%s(%s)' % (vol.display_name, vol.id))
                     for vol in volumes.values()],
            required=False)

    def handle(self, request, data):
        return True


class EditVolumeType(EditResource):
    def __init__(self, request, *args, **kwargs):
        super(EditVolumeType, self).__init__(request, *args, **kwargs)

        self.fields['other'] = forms.BooleanField(
            label=_("Select From Other Volume Type"),
            widget=forms.CheckboxInput(attrs={
                'class': 'switchable',
                'data-slug': 'volumetypes',
                'data-hide-on-checked': 'false'
            }),
            initial=False,
            required=False)
        vts = api.resource_list(self.request, constants.CINDER_VOL_TYPE)
        self.fields['volumetypes'] = forms.ChoiceField(
            label=_("Volume Type"),
            widget=forms.Select(attrs={
                'data-ori': self.detail.get('id'),
                'class': 'switched',
                'data-switch-on': 'volumetypes',
                'data-source-manual': _("Volume Type")
            }),
            initial=self.detail.get('id'),
            choices=[(vt.id, '%s(%s)' % (vt.name, vt.id))
                     for vt in vts],
            required=False)

    def handle(self, request, data):
        return True


class EditQos(EditResource):
    def __init__(self, request, *args, **kwargs):
        super(EditQos, self).__init__(request, *args, **kwargs)

        specs = self.properties.get('specs', {})
        self.fields['specs'] = forms.CharField(
            label=_("Specs"),
            widget=forms.Textarea(attrs={'rows': 4, 'readonly': 'readonly'}),
            initial='\n'.join(['%s=%s' % (k, v) for k, v in specs.items()]),
            required=False)

    def handle(self, request, data):
        return True


# OS::Net

class EditNet(EditResource):
    def __init__(self, request, *args, **kwargs):
        super(EditNet, self).__init__(request, *args, **kwargs)

        name = self.properties.get('name', '')
        self.fields['name'] = forms.CharField(
            label='Name',
            max_length=255,
            widget=forms.TextInput(attrs={'data-ori': name}),
            initial=name,
            required=False)
        admin_state = self.properties.get('admin_state_up', 'UP')
        self.fields['admin_state'] = forms.ChoiceField(
            choices=[(True, _('UP')),
                     (False, _('DOWN'))],
            label='Admin State',
            initial=admin_state,
            widget=forms.Select(attrs={'data-ori': admin_state == 'UP'}),
            required=False,
            help_text=_("The state to start"
                        " the network in."))
        shared = self.properties.get('shared', False)
        self.fields['shared'] = forms.BooleanField(
            label='Shared',
            initial=shared,
            widget=forms.CheckboxInput(attrs={'data-ori': shared}),
            required=False)

    def _other_nets(self):
        # Remove conflict network
        plan = api.plan_get(self.request, self.plan_id)
        dependencies = plan.updated_dependencies
        updated_res = plan.updated_resources
        rebuild_dependencies(dependencies)
        dep_servers = search_dependent_items(copy.deepcopy(dependencies),
                                             [self.res_id],
                                             'server')

        if not len(dep_servers):
            return

        value_specs = self.properties.get('value_specs', {})
        is_external = value_specs.get('router:external')
        tenant_id = self.request.user.tenant_id
        networks = api.net_list_for_tenant(self.request, tenant_id)
        networks = [network for network in networks
                    if (getattr(network, 'router:external') == is_external
                        and len(network.subnets) > 0)]
        dep_networks = search_dependent_items(copy.deepcopy(dependencies),
                                              dep_servers,
                                              'network',
                                              excepts=[self.res_id])

        networks = dict([(n.id, n) for n in networks])
        for dep_network in dep_networks:
            if updated_res[dep_network]['id'] in networks:
                del networks[updated_res[dep_network]['id']]
        self.fields['other'] = forms.BooleanField(
            label=_("Select From Other Networks"),
            widget=forms.CheckboxInput(attrs={
                'class': 'switchable',
                'data-slug': 'networks',
                'data-hide-on-checked': 'false'
            }),
            initial=False,
            required=False)
        self.fields['networks'] = forms.ChoiceField(
            label=_("Network"),
            widget=forms.Select(attrs={
                'data-ori': self.detail.get('id'),
                'class': 'switched',
                'data-switch-on': 'subnets',
                'data-source-manual': _("Network")
            }),
            initial=self.detail.get('id'),
            choices=[(n.id, '%s(%s)' % (n.name, n.id))
                     for n in networks.values()],
            required=False)

    def handle(self, request, data):
        return True


class EditSubnet(EditResource):
    def __init__(self, request, *args, **kwargs):
        super(EditSubnet, self).__init__(request, *args, **kwargs)

        name = self.properties.get('name', '')
        self.fields['name'] = forms.CharField(
            label='Name',
            max_length=255,
            widget=forms.TextInput(attrs={'data-ori': name}),
            initial=name,
            required=False)

        cidr = self.properties.get('cidr')
        self.fields['cidr'] = forms.IPField(
            label=_("Network Address"),
            required=False,
            initial=cidr,
            widget=forms.TextInput(
                attrs={
                    'data-ori': cidr,
                    'class': 'switched',
                    'data-switch-on': 'source',
                    'data-source-manual': _("Network Address"),}),
            help_text=_("Network address in CIDR format "
                        "(e.g. 192.168.0.0/24, 2001:DB8::/48)"),
            version=forms.IPv4 | forms.IPv6,
            mask=True)
        gateway_ip = self.properties.get('gateway_ip', '')
        self.fields['gateway_ip'] = forms.IPField(
            label=_("Gateway IP"),
            widget=forms.TextInput(attrs={
                'data-ori': gateway_ip,
                'class': 'switched',
                'data-switch-on': 'gateway_ip',
                'data-source-manual': _("Gateway IP")
            }),
            required=False,
            initial=gateway_ip,
            help_text=_("IP address of Gateway (e.g. 192.168.0.254) "
                        "The default value is the first IP of the "
                        "network address "
                        "(e.g. 192.168.0.1 for 192.168.0.0/24, "
                        "2001:DB8::1 for 2001:DB8::/48). "
                        "If you use the default, leave blank. "
                        "If you do not want to use a gateway, "
                        "check 'Disable Gateway' below."),
            version=forms.IPv4 | forms.IPv6,
            mask=False)
        no_gateway = self.properties.get('no_gateway', False)
        self.fields['no_gateway'] = forms.BooleanField(
            label=_("Disable Gateway"),
            widget=forms.CheckboxInput(
                attrs={'data-ori': no_gateway,
                       'class': 'switchable',
                       'data-slug': 'gateway_ip',
                       'data-hide-on-checked': 'true'
                       }),
            initial=no_gateway,
            required=False)

        enable_dhcp = self.properties.get('enable_dhcp', True)
        self.fields['enable_dhcp'] = forms.BooleanField(
            label=_("Enable DHCP"),
            widget=forms.CheckboxInput(attrs={'data-ori': enable_dhcp}),
            initial=enable_dhcp,
            required=False)

        pools = self.properties.get('allocation_pools', [])
        pools = '\n'.join(['%s,%s' % (p['start'], p['end']) for p in pools])
        self.fields['allocation_pools'] = forms.CharField(
            label=_("Allocation Pools"),
            widget=forms.Textarea(attrs={'rows': 4, 'data-ori': pools}),
            initial=pools,
            required=False)

        dns = '\n'.join(self.properties.get('dns_nameservers', []))
        self.fields['dns_nameservers'] = forms.CharField(
            label=_("DNS Name Servers"),
            widget=forms.Textarea(attrs={'rows': 4, 'data-ori': dns}),
            initial=dns,
            required=False)

        host_routes = self.properties.get('host_routes', [])
        routes = '\n'.join(['%s,%s' % (r['destination'], r['nexthop'])
                            for r in host_routes])
        self.fields['host_routes'] = forms.CharField(
            label=_("Host Routes"),
            widget=forms.Textarea(attrs={'rows': 4, 'data-ori': routes}),
            initial=routes,
            required=False)

        self._other_subnet()

    def _other_subnet(self):
        # Remove conflict subnet.
        plan = api.plan_get(self.request, self.plan_id)
        dependencies = plan.updated_dependencies
        updated_res = plan.updated_resources
        rebuild_dependencies(dependencies)
        dep_servers = search_dependent_items(copy.deepcopy(dependencies),
                                             [self.res_id],
                                             'server')
        if not len(dep_servers):
            return

        tenant_id = self.request.user.tenant_id
        subnets = api.subnet_list_for_tenant(self.request, tenant_id)

        # TODO(drngsl) NOTE(critical) the 'from_network_id' will never show in
        # properties, so we will always extract subnets from all networks
        if 'from_network_id' in self.properties:
            subnets = [subnet for subnet in subnets
                       if subnet.network_id ==
                       self.properties.get('from_network_id')]
        dep_subnets = search_dependent_items(copy.deepcopy(dependencies),
                                             dep_servers,
                                             'subnet',
                                             excepts=[self.res_id])
        subnets = dict([(s.id, s) for s in subnets])
        for dep_subnet in dep_subnets:
            if updated_res[dep_subnet]['id'] in subnets:
                del subnets[updated_res[dep_subnet]['id']]
        self.fields['other'] = forms.BooleanField(
            label=_("Select From Other Subnets"),
            widget=forms.CheckboxInput(attrs={
                'class': 'switchable',
                'data-slug': 'subnets',
                'data-hide-on-checked': 'false'
            }),
            initial=False,
            required=False)
        self.fields['subnets'] = forms.ChoiceField(
            label=_("Subnet"),
            widget=forms.Select(attrs={
                'data-ori': self.detail.get('id'),
                'class': 'switched',
                'data-switch-on': 'subnets',
                'data-source-manual': _("Subnet")
            }),
            initial=self.detail.get('id'),
            choices=[(sn.id, '%s(%s)' % (sn.name, sn.id))
                     for sn in subnets.values()],
            required=False)

    def handle(self, request, data):
        return True


class EditPort(forms.SelfHandlingForm):
    def __init__(self, request, *args, **kwargs):
        super(EditPort, self).__init__(request, *args, **kwargs)
        pass

    def handle(self, request, data):
        return True


class EditSecurityGroup(forms.SelfHandlingForm):
    def __init__(self, request, *args, **kwargs):
        super(EditSecurityGroup, self).__init__(request, *args, **kwargs)
        pass

    def handle(self, request, data):
        return True


class EditRouter(forms.SelfHandlingForm):
    def __init__(self, request, *args, **kwargs):
        super(EditRouter, self).__init__(request, *args, **kwargs)
        pass

    def handle(self, request, data):
        return True
