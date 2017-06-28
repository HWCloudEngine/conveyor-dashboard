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
    def allowed(self, request, net=None):
        return net.status in resource_state.NET_CLONE_STATE


def get_subnets(network):
    template_name = 'networks/_network_ips.html'
    context = {"subnets": network.subnets}
    return template.loader.render_to_string(template_name, context)


DISPLAY_CHOICES = (
    ("up", pgettext_lazy("Admin state of a Network", u"UP")),
    ("down", pgettext_lazy("Admin state of a Network", u"DOWN")),
)
STATUS_DISPLAY_CHOICES = (
    ("active", pgettext_lazy("Current status of a Network", u"Active")),
)


class NetworksFilterAction(tables.FilterAction):
    def filter(self, table, networks, filter_string):
        """Naive case-insensitive search."""
        query = filter_string.lower()
        return [network for network in networks
                if query in network.name.lower()]


class NetworksTable(tables.DataTable):
    name = tables.Column("name_or_id",
                         verbose_name=_("Name"),
                         link='horizon:project:networks:detail')
    subnets = tables.Column(get_subnets,
                            verbose_name=_("Subnets Associated"),)
    shared = tables.Column("shared", verbose_name=_("Shared"),
                           filters=(filters.yesno, filters.capfirst))
    external = tables.Column("router:external", verbose_name=_("External"),
                             filters=(filters.yesno, filters.capfirst))
    status = tables.Column("status", verbose_name=_("Status"),
                           display_choices=STATUS_DISPLAY_CHOICES)
    admin_state = tables.Column("admin_state",
                                verbose_name=_("Admin State"),
                                display_choices=DISPLAY_CHOICES)

    class Meta(object):
        name = 'networks'
        verbose_name = _("Networks")
        css_classes = "table-res %s" % consts.NEUTRON_NET
        table_actions = (common_actions.CreatePlanWithMultiRes,
                         NetworksFilterAction)
        row_actions = (CreatePlan,)
