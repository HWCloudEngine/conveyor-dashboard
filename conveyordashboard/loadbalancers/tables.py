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

from django import template
from django.template import defaultfilters as filters
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from conveyordashboard.common import actions as common_actions
from conveyordashboard.common import constants as consts
from conveyordashboard.common import resource_state


class CreatePlan(common_actions.CreatePlan):
    def allowed(self, request, pool=None):
        return pool.status in resource_state.POOL_CLONE_STATE


STATUS_CHOICES = (
    ("Active", True),
)


STATUS_DISPLAY_CHOICES = (
    ("Active", pgettext_lazy("Current status of a Pool",
                             u"Active")),
)


ADMIN_STATE_DISPLAY_CHOICES = (
    ("UP", pgettext_lazy("Admin state of a Load balancer", u"UP")),
    ("DOWN", pgettext_lazy("Admin state of a Load balancer", u"DOWN")),
)


def get_vip_name(pool):
    if hasattr(pool, "vip") and pool.vip:
        template_name = 'project/loadbalancers/_pool_table_vip_cell.html'
        context = {"vip": pool.vip, }
        return template.loader.render_to_string(template_name, context)
    else:
        return None


def get_subnet(pool):
    if hasattr(pool, "subnet") and pool.subnet:
        template_name = 'project/loadbalancers/_pool_table_subnet_cell.html'
        context = {"subnet": pool.subnet}
        return template.loader.render_to_string(template_name, context)
    else:
        return None


class PoolsTable(tables.DataTable):
    METHOD_DISPLAY_CHOICES = (
        ("round_robin", pgettext_lazy("load balancing method",
                                      u"Round Robin")),
        ("least_connections", pgettext_lazy("load balancing method",
                                            u"Least Connections")),
        ("source_ip", pgettext_lazy("load balancing method",
                                    u"Source IP")),
    )

    name = tables.Column("name_or_id",
                         verbose_name=_("Name"),
                         link="horizon:project:loadbalancers:pooldetails")
    description = tables.Column('description', verbose_name=_("Description"))
    provider = tables.Column('provider', verbose_name=_("Provider"),
                             filters=(lambda v: filters.default(v, _('N/A')),))
    subnet_name = tables.Column(get_subnet, verbose_name=_("Subnet"))
    protocol = tables.Column('protocol', verbose_name=_("Protocol"))
    method = tables.Column('lb_method',
                           verbose_name=_("LB Method"),
                           display_choices=METHOD_DISPLAY_CHOICES)
    status = tables.Column('status',
                           verbose_name=_("Status"),
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)
    vip_name = tables.Column(get_vip_name, verbose_name=_("VIP"))
    admin_state = tables.Column("admin_state",
                                verbose_name=_("Admin State"),
                                display_choices=ADMIN_STATE_DISPLAY_CHOICES)

    class Meta(object):
        name = "poolstable"
        verbose_name = _("Pools")
        css_classes = ' '.join(['table-res', consts.NEUTRON_POOL])
        table_actions = (common_actions.CreatePlanWithMultiRes,)
        row_actions = (CreatePlan,)
