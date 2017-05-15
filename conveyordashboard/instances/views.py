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

from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables
from oslo_log import log as logging

from conveyordashboard.api import api
from conveyordashboard.common import constants as consts
from conveyordashboard.instances import tables as inst_tables

LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = inst_tables.InstancesTable
    template_name = '_res_table.html'
    page_title = _("Instances")

    def has_more_data(self, table):
        return self._more

    def get_data(self):
        marker = self.request.GET.get(
            inst_tables.InstancesTable._meta.pagination_param, None)
        search_opts = self.get_filters({'marker': marker, 'paginate': True})
        # Gather our instances
        try:
            instances, self._more = api.server_list(self.request,
                                                    search_opts=search_opts)
        except Exception:
            self._more = False
            instances = []
            exceptions.handle(self.request,
                              _("Unable to retrieve instances."))

        if instances:
            # try:
            #     os_api.network.servers_update_addresses(self.request,
            #                                             instances)
            # except Exception:
            #     exceptions.handle(
            #         self.request,
            #         message=_("Unable to retrieve IP addresses "
            #                   "from Neutron."),
            #         ignore=True)

            try:
                flavors = api.resource_list(self.request, consts.NOVA_FLAVOR)
            except Exception:
                flavors = []
                exceptions.handle(self.request, ignore=True)

            try:
                images = api.resource_list(self.request, consts.GLANCE_IMAGE)
            except Exception:
                images = []
                exceptions.handle(self.request, ignore=True)

            full_flavors = SortedDict([(str(flavor.id), flavor)
                                       for flavor in flavors])
            image_map = SortedDict([(str(image.id), image)
                                    for image in images])

            # Loop through instances to get flavor info.
            for instance in instances:
                if hasattr(instance, 'image'):
                    # Instance from image returns dict
                    if isinstance(instance.image, dict):
                        if instance.image.get('id') in image_map:
                            instance.image = image_map[instance.image['id']]

                try:
                    flavor_id = instance.flavor['id']
                    if flavor_id in full_flavors:
                        instance.full_flavor = full_flavors[flavor_id]
                    else:
                        instance.full_flavor = api.resource_detail(
                            self.request,
                            consts.NOVA_FLAVOR,
                            flavor_id)
                except Exception:
                    msg = ('Unable to retrieve flavor "%s" for instance "%s".'
                           % (flavor_id, instance.id))
                    LOG.info(msg)
        return instances

    def get_filters(self, filters):
        filter_action = self.table._meta._filter_action
        if filter_action:
            filter_field = self.table.get_filter_field()
            if filter_action.is_api_filter(filter_field):
                filter_string = self.table.get_filter_string()
                if filter_field and filter_string:
                    filters[filter_field] = filter_string
        return filters
