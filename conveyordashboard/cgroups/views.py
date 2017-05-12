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
from conveyordashboard.common import constants as consts
from conveyordashboard.cgroups import tables as cgroup_tables


class IndexView(tables.DataTableView):
    table_class = cgroup_tables.VolumeCGroupsTable
    template_name = 'cgroups/index.html'
    page_title = _("Consistency Groups")

    def get_data(self):
        cgroups = []
        try:
            cgroups = api.resource_list(self.request,
                                        consts.CINDER_CONSISGROUP)
        except Exception:
            exceptions.handle(self.request, _("Unable to retrieve "
                                              "volume consistency groups."))
        return cgroups
