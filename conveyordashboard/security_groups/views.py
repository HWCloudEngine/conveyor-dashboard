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
from horizon import tables

from conveyordashboard.api import api
from conveyordashboard.security_groups import tables as secgroup_tables


class IndexView(tables.DataTableView):
    table_class = secgroup_tables.SecurityGroupsTable
    template_name = 'security_groups/index.html'
    page_title = _("Security Groups")

    def get_data(self):
        try:
            secgroups = api.sg_list(self.request, self.request.user.tenant_id)
        except Exception:
            secgroups = []
            exceptions.handle(self.request,
                              _('Unable to retrieve security groups.'))
        return sorted(secgroups, key=lambda group: group.name)
