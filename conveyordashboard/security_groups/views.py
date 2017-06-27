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
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tables

from conveyordashboard.api import api
from conveyordashboard.security_groups import forms as secgroup_forms
from conveyordashboard.security_groups import tables as secgroup_tables


class IndexView(tables.DataTableView):
    table_class = secgroup_tables.SecurityGroupsTable
    template_name = '_res_table.html'
    page_title = _("Security Groups")

    def get_data(self):
        try:
            secgroups = api.sg_list(self.request, self.request.user.tenant_id)
        except Exception:
            secgroups = []
            exceptions.handle(self.request,
                              _('Unable to retrieve security groups.'))
        return sorted(secgroups, key=lambda group: group.name)


class AddRuleView(forms.ModalFormView):
    form_class = secgroup_forms.AddRule
    form_id = 'create_security_group_rule_form'
    modal_header = _("Add Rule")
    modal_id = 'create_security_group_rule_modal'
    template_name = 'security_groups/add_rule.html'
    ajax_template_name = 'security_groups/add_rule.html'
    submit_label = _("Add")
    submit_url = "horizon:conveyor:security_groups:add_rule"
    url = "horizon:conveyor:security_groups:index"
    page_title = _("Add Rule")

    def get_form_kwargs(self):
        kwargs = super(AddRuleView, self).get_form_kwargs()

        try:
            tenant_id = self.request.user.tenant_id
            groups = api.sg_list(self.request, tenant_id=tenant_id)
        except Exception:
            groups = []
            exceptions.handle(self.request,
                              _("Unable to retrieve security groups."))

        curr_sg_id = self.request.GET.get('security_group_id', '')

        security_groups = []
        for group in groups:
            if group.id == curr_sg_id:
                security_groups.append((group.id,
                                        _("%s (current)") % group.name))
            else:
                security_groups.append((group.id, group.name))
        kwargs['sg_list'] = security_groups
        return kwargs
