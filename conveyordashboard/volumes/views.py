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
from conveyordashboard.common import resource_state
from conveyordashboard.volumes import tables as volume_tables


class IndexView(tables.DataTableView):
    table_class = volume_tables.VolumesTable
    template_name = '_res_table.html'
    page_title = _("Volumes")

    def get_data(self):
        volumes = []
        try:
            volumes = api.volume_list(self.request)
            volumes = filter(self._status_filter, volumes)
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve volumes list."))
        return volumes

    def _status_filter(self, volume):
        return volume.status in resource_state.VOLUME_CLONE_STATE \
            or volume.status in resource_state.VOLUME_MIGRATE_STATE

    def get_filters(self, filters):
        filter_action = self.table._meta._filter_action
        if filter_action:
            filter_field = self.table.get_filter_field()
            if filter_action.is_api_filter(filter_field):
                filter_string = self.table.get_filter_string()
                if filter_field and filter_string:
                    filters[filter_field] = filter_string
        return filters
