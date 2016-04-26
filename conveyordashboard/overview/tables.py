import logging

from django import template
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.template import defaultfilters as filters
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from openstack_dashboard.dashboards.project.instances.tables\
            import InstancesTable
from openstack_dashboard.dashboards.project.networks.tables\
            import NetworksTable
from openstack_dashboard.dashboards.project.networks.subnets.tables\
            import SubnetsTable
from openstack_dashboard.dashboards.project.routers.tables import RoutersTable
from openstack_dashboard.dashboards.project.volumes.volumes.tables\
            import VolumesTable

LOG =logging.getLogger(__name__)


def get_res_type(table):
    css_classes = table.css_classes()
    for css_cls in css_classes.split(" "):
        if css_cls.startswith("OS::"):
            return css_cls
    return ""


class CreateClonePlan(tables.LinkAction):
    name = "clone_plan"
    verbose_name = _("Create Clone Plan")
    url = "horizon:conveyor:overview:create_plan"
    classes = ("ajax-modal", "btn-default", "btn-clone")
    help_text = _("Execute clone plan")

    def get_link_url(self, datum):
        #LOG.info("full_url={}".format(self.table.get_full_url()))
        base_url = reverse(self.url)
        if self.table.kwargs.get("next_url", None):
            next_url = self.table.kwargs["next_url"]
        else:
            next_url = self.table.get_full_url()

        params = urlencode({"ids": get_res_type(self.table) + "*"
                                    + self.table.get_object_id(datum),
                            "type": "clone",
                            "next_url": next_url})
        return "?".join([base_url, params])


class CreateMigratePlan(tables.LinkAction):
    name = "migrate_plan"
    verbose_name = _("Create Migrate Plan")
    url = "horizon:conveyor:overview:create_plan"
    classes = ("ajax-modal", "btn-default", "btn-clone")
    help_text = _("Execute migrate plan")

    def get_link_url(self, datum):
        #LOG.info("full_url={}".format(self.table.get_full_url()))
        base_url = reverse(self.url)
        if self.table.kwargs.get("next_url", None):
            next_url = self.table.kwargs["next_url"]
        else:
            next_url = self.table.get_full_url()

        params = urlencode({"ids": get_res_type(self.table) + "*"
                                    + self.table.get_object_id(datum),
                            "type": "migrate",
                            "next_url": next_url})
        return "?".join([base_url, params])


class CreatePlanWithMulRes(tables.LinkAction):
    name = "create_plan_with_mul_res"
    verbose_name = _("Create Clone Plan")
    url = "horizon:conveyor:overview:create_plan"
    classes = ("ajax-modal", "btn-default", 
               "create-plan-for-mul-sel", "disabled")
    help_text = _("Create clone plan with selecting multi-resources")
    icon = "plus"


class CreateMigratePlanWithMulRes(tables.LinkAction):
    name = "create_migrate_plan_with_mul_res"
    verbose_name = _("Create Migrate Plan")
    url = "horizon:conveyor:overview:create_plan"
    classes = ("ajax-modal", "btn-default", 
               "create-migrate-plan-for-mul-sel", "disabled")
    help_text = _("Create migrate plan with selecting multi-resources")
    icon = "plus"
    

class InstanceFilterAction(tables.FilterAction):
    def filter(self, table, instances, filter_string):
        q = filter_string.lower()

        def comp(instance):
            return q in instance.name.lower()

        return filter(comp, instances)


class InstancesTable(InstancesTable):
    class Meta(object):
        name = "instances"
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
        super(VolumesTable, self).__init__(request,
           data=data,
           needs_form_wrapper=needs_form_wrapper,
           **kwargs)
        del self.columns["recovered_volume_id"]
        del self.columns["recover_status"]

    class Meta(object):
        name = "volumes"
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
        name = "networks"
        hidden_title = False
        verbose_name = _("Networks")
        css_classes = "table-res OS::Neutron::Net"
        table_actions = (NetworksFilterAction,)


class SubnetsTable(SubnetsTable):
    class Meta(object):
        name = "subnets"
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
        del self.columns["ext_net"]

    class Meta(object):
        name = "routers"
        hidden_title = False
        varbose_name = _("Routers")
        css_classes = "table-res OS::Neutron::Router"
        table_actions = (NetworksFilterAction,)

 
class ActionsTable(tables.DataTable):
    class Meta(object):
        name = "actions"
        verbose_name = _("Actions")
        table_actions = (CreatePlanWithMulRes, CreateMigratePlanWithMulRes,)
