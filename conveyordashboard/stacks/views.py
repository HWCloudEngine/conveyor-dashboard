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
from horizon.utils import memoized

from conveyordashboard.api import api
from conveyordashboard.stacks import tables as stacks_tables


class IndexView(tables.DataTableView):
    table_class = stacks_tables.StacksTable
    template_name = 'stacks/index.html'
    page_title = _("Stacks")

    @memoized.memoized_method
    def get_data(self):
        stacks = []
        marker = self.request.GET.get(
            stacks_tables.StacksTable._meta.pagination_param, None)
        try:
            stacks = api.stack_list(self.request)
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve stacks."))
        return stacks

    def get_filters(self, filters):
        filter_action = self.table._meta._filter_action
        if filter_action:
            filter_field = self.table.get_filter_field()
            if filter_action.is_api_filter(filter_field):
                filter_string = self.table.get_filter_string()
                if filter_field and filter_string:
                    filters[filter_field] = filter_string
        return filters
