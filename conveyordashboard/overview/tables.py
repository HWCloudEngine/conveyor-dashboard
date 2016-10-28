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
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from openstack_dashboard.dashboards.project.instances.tables \
    import InstancesTable
from openstack_dashboard.dashboards.project.networks.subnets.tables \
    import SubnetsTable
from openstack_dashboard.dashboards.project.networks.tables \
    import NetworksTable
from openstack_dashboard.dashboards.project.routers.tables import RoutersTable
from openstack_dashboard.dashboards.project.volumes.volumes.tables \
    import VolumesTable
from openstack_dashboard.dashboards.project.loadbalancers.tables import PoolsTable    
from openstack_dashboard.dashboards.project.access_and_security.\
    floating_ips.tables import FloatingIPsTable
from openstack_dashboard.dashboards.project.access_and_security.\
    security_groups.tables import SecurityGroupsTable    

LOG = logging.getLogger(__name__)


def get_res_type(datum, table):
    if hasattr(datum, 'res_type'):
        return datum.res_type
    css_classes = table.css_classes()
    for css_cls in css_classes.split(' '):
        if css_cls.startswith('OS::'):
            return css_cls
    return ''


class CreateClonePlan(tables.LinkAction):
    name = 'clone_plan'
    verbose_name = _("Create Clone Plan")
    url = 'horizon:conveyor:plans:clone'
    classes = ("ajax-modal", "btn-default", "btn-clone")
    help_text = _("Execute clone plan")

    def get_link_url(self, datum):
        base_url = reverse(self.url)
        if self.table.kwargs.get('next_url', None):
            next_url = self.table.kwargs['next_url']
        else:
            next_url = self.table.get_full_url()

        params = urlencode({'ids': ''.join([get_res_type(datum, self.table),
                                            '*',
                                            self.table.get_object_id(datum)]),
                            'next_url': next_url})
        return '?'.join([base_url, params])


class CreateMigratePlan(tables.LinkAction):
    name = 'migrate_plan'
    verbose_name = _("Create Migrate Plan")
    url = 'horizon:conveyor:plans:migrate'
    classes = ("ajax-modal", "btn-default", "btn-migrate")
    help_text = _("Execute migrate plan")

    def get_link_url(self, datum):
        base_url = reverse(self.url)

        params = urlencode({'ids': ''.join([get_res_type(datum, self.table),
                                            '*',
                                            self.table.get_object_id(datum)])})
        return '?'.join([base_url, params])


class CreatePlanWithMulRes(tables.LinkAction):
    name = 'create_plan_with_mul_res'
    verbose_name = _("Create Clone Plan")
    url = 'horizon:conveyor:plans:clone'
    classes = ("ajax-modal", "btn-default",
               "create-plan-for-mul-sel", "disabled")
    help_text = _("Create clone plan with selecting multi-resources")
    icon = 'plus'


class CreateMigratePlanWithMulRes(tables.LinkAction):
    name = 'create_migrate_plan_with_mul_res'
    verbose_name = _("Create Migrate Plan")
    url = 'horizon:conveyor:plans:migrate'
    classes = ("ajax-modal", "btn-default",
               "create-migrate-plan-for-mul-sel", "disabled")
    help_text = _("Create migrate plan with selecting multi-resources")
    icon = 'plus'


class InstanceFilterAction(tables.FilterAction):
    def filter(self, table, instances, filter_string):
        q = filter_string.lower()

        def comp(instance):
            return q in instance.name.lower()

        return filter(comp, instances)


class InstancesTable(InstancesTable):
    class Meta(object):
        name = 'instances'
        hidden_title = False
        verbose_name = _("Instances")
        css_classes = "table-res OS::Nova::Server"
        table_actions = (InstanceFilterAction,)


class VolumeFilterAction(tables.FilterAction):
    def filter(self, table, volumes, filter_string):
        q = filter_string.lower()

        def comp(volume):
            return q in volume.name.lower()

        return filter(comp, volumes)


class VolumesTable(VolumesTable):
    def __init__(self, request, data=None, needs_form_wrapper=None, **kwargs):
        super(VolumesTable, self)\
            .__init__(request, data=data,
                      needs_form_wrapper=needs_form_wrapper,
                      **kwargs)
        del self.columns['recovered_volume_id']
        del self.columns['recover_status']

    class Meta(object):
        name = 'volumes'
        hidden_title = False
        verbose_name = _("Volumes")
        css_classes = "table-res OS::Cinder::Volume"
        table_actions = (VolumeFilterAction,)


class NetworksFilterAction(tables.FilterAction):
    def filter(self, table, networks, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [network for network in networks
                if query in network.name.lower()]


class NetworksTable(NetworksTable):
    class Meta(object):
        name = 'networks'
        hidden_title = False
        verbose_name = _("Networks")
        css_classes = "table-res OS::Neutron::Net"
        table_actions = (NetworksFilterAction,)


class SecurityGroupFilterAction(tables.FilterAction):
    def filter(self, table, SecurityGroups, filter_string):
        q = filter_string.lower()

        def comp(SecurityGroup):
            return q in SecurityGroup.name.lower()

        return filter(comp, SecurityGroups)
                           
class SecurityGroupsTable(SecurityGroupsTable):
    class Meta(object):
        name = 'security_groups'
        hidden_title = False
        verbose_name = _("Security Groups")
        css_classes = "table-res OS::Neutron::SecurityGroup"
        table_actions = (SecurityGroupFilterAction,)

class FloatingIPFilterAction(tables.FilterAction):
    def filter(self, table, FloatingIPs, filter_string):
        q = filter_string.lower()

        def comp(FloatingIP):
            return q in FloatingIP.name.lower()

        return filter(comp, FloatingIPs)
    
class FloatingIPsTable(FloatingIPsTable):
    ip = tables.Column("floating_ip_address",
                       verbose_name=_("IP Address"),
                       attrs={'data-type': "ip"})
    fixed_ip = tables.Column('fixed_ip_address',
                             verbose_name=_("Mapped Fixed IP Address"))
    pool = tables.Column("floating_network_id",
                         verbose_name=_("Pool"))

    def get_object_display(self, datum):
        return datum.floating_ip_address

    class Meta(object):
        name = 'floating_ips'
        hidden_title = False
        verbose_name = _("Floating IPs")
        css_classes = "table-res OS::Neutron::FloatingIP"
        table_actions = (FloatingIPFilterAction,)     


class PoolFilterAction(tables.FilterAction):
    def filter(self, table, pools, filter_string):
        q = filter_string.lower()

        def comp(pool):
            return q in pool.name.lower()

        return filter(comp, pools)


class PoolsTable(PoolsTable):
    class Meta(object):
        name = "pools"
        hidden_title = False
        verbose_name = _("Pools")
        css_classes = "table-res OS::Neutron::Pool"
        table_actions = (PoolFilterAction,)        
                  

class SubnetsTable(SubnetsTable):
    class Meta(object):
        name = 'subnets'
        hidden_title = False
        verbose_name = _("Subnets")
        css_classes = "table-res OS::Neutron::Subnet"
        table_actions = (NetworksFilterAction,)


class RoutersTable(RoutersTable):
    def __init__(self, request, data=None, needs_form_wrapper=None, **kwargs):
        super(RoutersTable, self).__init__(
            request,
            data=data,
            needs_form_wrapper=needs_form_wrapper,
            **kwargs)
        del self.columns['ext_net']

    class Meta(object):
        name = 'routers'
        hidden_title = False
        varbose_name = _("Routers")
        css_classes = "table-res OS::Neutron::Router"
        table_actions = (NetworksFilterAction,)


class ActionsTable(tables.DataTable):
    class Meta(object):
        name = 'actions'
        verbose_name = _("Actions")
        table_actions = (CreatePlanWithMulRes, CreateMigratePlanWithMulRes,)


class ResTable(tables.DataTable):
    project_id = tables.Column('project_id', verbose_name=_("Project ID"),
                               hidden=True)
    name = tables.Column("name", verbose_name=_("Name"))
    res_type = tables.Column("res_type", verbose_name=_("Resource Type"))

    class Meta(object):
        name = 'resource'
        verbose_name = _("Resource")
        table_actions = (CreatePlanWithMulRes,
                         CreateMigratePlanWithMulRes)
        row_actions = (CreateClonePlan, CreateMigratePlan)