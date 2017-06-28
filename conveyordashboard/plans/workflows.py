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

import six

from oslo_utils import strutils

import json

from django.utils.translation import ugettext_lazy as _

from horizon import forms
from horizon import workflows

from oslo_log import log

from conveyordashboard.api import api
from conveyordashboard.common import constants
from conveyordashboard.plans import tables as plan_tables

LOG = log.getLogger(__name__)

TAG_RES_TYPE = constants.TAG_RES_TYPE


class ResourceInfoAction(workflows.Action):
    availability_zone_map = forms.CharField(widget=forms.HiddenInput,
                                            required=False)
    clone_resources = forms.CharField(widget=forms.HiddenInput,
                                      required=False,
                                      initial='[]')
    clone_links = forms.CharField(widget=forms.HiddenInput,
                                  required=False,
                                  initial='[]')
    update_resources = forms.CharField(widget=forms.HiddenInput,
                                       required=False,
                                       initial='[]')
    replace_resources = forms.CharField(widget=forms.HiddenInput,
                                        required=False,
                                        initial='[]')

    def __init__(self, request, context, *args, **kwargs):
        super(ResourceInfoAction, self).__init__(request, context,
                                                 *args, **kwargs)

    def clean(self):
        cleaned_data = super(ResourceInfoAction, self).clean()
        return cleaned_data

    class Meta(object):
        name = _("Plan Resources")


class ResourceInfo(workflows.Step):
    template_name = "plans/_workflow_step_edit_plan_resources.html"
    action_class = ResourceInfoAction
    depends_on = ('plan_id',)
    contributes = ('availability_zone_map', 'clone_resources',
                   'clone_links', 'update_resources', 'replace_resources')

    def __init__(self, workflow):
        super(ResourceInfo, self).__init__(workflow)

        request = workflow.request
        plan_id = request.resolver_match.kwargs['plan_id']
        self.plan_id = plan_id

        plan_res_azs = api.list_clone_resources_attribute(request,
                                                          plan_id,
                                                          'availability_zone')

        az_map = {}
        for az in plan_res_azs:
            az_map[az] = request.GET.get(az)
        self.az_map = az_map
        topo = api.build_resources_topo(request, plan_id, az_map)
        plan_deps_table = plan_tables.PlanDepsTable(
            request,
            plan_tables.trans_plan_deps(topo),
            plan_id=plan_id,
            plan_type=constants.CLONE)
        self.plan_deps_table = plan_deps_table.render()

        self.d3_data = json.dumps(topo)

    def prepare_action_context(self, request, context):
        context['availability_zone_map'] = json.dumps(self.az_map)
        return context

    def contribute(self, data, context):
        context.update(data)
        return context


class PlanInfoAction(workflows.Action):
    incremental_clone = forms.BooleanField(label=_("Incremental Clone"),
                                           initial=True,
                                           required=False)
    sys_clone = forms.BooleanField(label=_("Clone System Volume"),
                                   required=False,
                                   initial=False)
    copy_data = forms.BooleanField(label=_("Copy Volume Data"),
                                   required=False,
                                   initial=True)

    class Meta(object):
        name = _("Plan Information")
        help_text = _('Setting specific field for cloning or migrate plan.')


class PlanInfo(workflows.Step):
    action_class = PlanInfoAction
    contributes = ('sys_clone', 'copy_data')


def preprocess_update_resources(update_resources):

    for res in update_resources:
        res_type = res[TAG_RES_TYPE]
        if res_type == constants.NOVA_SERVER:
            if isinstance(res.get('metadata'), six.string_types):
                meta = [dict(zip(['k', 'v'], item.strip().split('=')))
                        for item in res['metadata'].split('\n')
                        if item.strip()]
                res['metadata'] = dict((i['k'], i.get('v', '')) for i in meta)
        elif res_type == constants.CINDER_VOLUME:
            if isinstance(res.get('metadata'), six.string_types):
                meta = [dict(zip(['k', 'v'], item.strip().split('=')))
                        for item in res['metadata'].split('\n')
                        if item.strip()]
                res['metadata'] = dict((i['k'], i.get('v', '')) for i in meta)
            if 'size' in res:
                res['size'] = int(res['size'])
        elif res_type == constants.NEUTRON_SUBNET:
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
        elif res_type == constants.NEUTRON_NET:
            if 'value_specs' in res:
                val_specs = res['value_specs']
                if 'router_external' in val_specs:
                    val_specs['router:external'] = strutils.bool_from_string(
                        val_specs.pop('router_external'))
                if 'segmentation_id' in val_specs:
                    val_specs['provider:segmentation_id'] \
                        = int(val_specs.pop('segmentation_id'))
                if 'physical_network' in val_specs:
                    val_specs['provider:physical_network'] \
                        = val_specs.pop('physical_network')
                if 'network_type' in val_specs:
                    val_specs['provider:network_type'] \
                        = val_specs.pop('network_type')
            if 'admin_state_up' in res:
                res['admin_state_up'] \
                    = strutils.bool_from_string(res['admin_state_up'])
        elif res_type == constants.NEUTRON_SECGROUP:
            if 'rules' in res:
                rules = res['rules']
                if isinstance(rules, six.string_types):
                    rules = json.JSONDecoder().decode(rules)
                for r in rules:
                    r.pop('id', None)
                res['rules'] = rules
        elif res_type == constants.NEUTRON_FLOATINGIP:
            # NOTE: In heat, there is not floating_network_id property.
            res.pop('floating_network_id')


class ClonePlan(workflows.Workflow):
    slug = "clone_plan"
    name = _("Clone Plan")
    # template_name = "plans/_workflow_clone_plan.html"
    finalize_button_name = _("Clone")
    success_message = _('Cloned plan "%s".')
    failure_message = _('Unable to clone plan "%s".')
    success_url = "horizon:conveyor:plans:index"
    default_steps = (ResourceInfo,
                     PlanInfo)

    def handle(self, request, context):
        plan_id = context['plan_id']
        availability_zone_map = json.loads(context['availability_zone_map'])
        clone_resources = json.loads(context['clone_resources'])
        clone_links = json.loads(context['clone_links'])
        update_resources = json.loads(context['update_resources'])
        sys_clone = context['sys_clone']
        copy_data = context['copy_data']
        preprocess_update_resources(update_resources)
        api.clone(request, plan_id, availability_zone_map, clone_resources,
                  clone_links=clone_links, update_resources=update_resources,
                  sys_clone=sys_clone, copy_data=copy_data)
        return True
