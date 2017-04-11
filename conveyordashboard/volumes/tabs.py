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
from horizon import tabs

from openstack_dashboard import api as os_api
from openstack_dashboard import policy

from conveyordashboard.api import api
from conveyordashboard.common import constants
from conveyordashboard.volumes import tables as volume_tables


class PagedTableMixin(object):
    def __init__(self, *args, **kwargs):
        super(PagedTableMixin, self).__init__(*args, **kwargs)
        self._has_prev_data = False
        self._has_more_data = False

    def has_prev_data(self, table):
        return self._has_prev_data

    def has_more_data(self, table):
        return self._has_more_data

    def _get_marker(self):
        meta = self.table_classes[0]._meta
        prev_marker = self.request.GET.get(meta.prev_pagination_param, None)
        if prev_marker:
            return prev_marker, "asc"
        else:
            marker = self.request.GET.get(meta.pagination_param, None)
            if marker:
                return marker, "desc"
            return None, "desc"


# class VolumeTab(PagedTableMixin, tabs.TableTab, VolumeTableMixIn):
class VolumeTab(tabs.TableTab):
    table_classes = (volume_tables.VolumesTable,)
    name = _("Volumes")
    slug = "volumes_tab"
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def _get_volumes(self, search_opts=None):
        volumes = []
        try:
            volumes = api.resource_list(self.request, constants.CINDER_VOLUME)
            volumes = [os_api.cinder.Volume(v) for v in volumes]
        except Exception:
            exceptions.handle(self.request,
                              _("Unable to retrieve volumes list."))
        return volumes

    def get_volumes_data(self):
        volumes = self._get_volumes()
        # attached_instance_ids = self._get_attached_instance_ids(volumes)
        # instances = self._get_instances(instance_ids=attached_instance_ids)
        # volume_ids_with_snapshots = self._get_volumes_ids_with_snapshots()
        # self._set_volume_attributes(
        #     volumes, instances, volume_ids_with_snapshots)
        return volumes


class CGroupsTab(tabs.TableTab):
    table_classes = (volume_tables.VolumeCGroupsTable,)
    name = _("Volume Consistency Groups")
    slug = "cgroups_tab"
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def allowed(self, request):
        return policy.check(
            (("volume", "consistencygroup:get_all"),),
            request
        )

    def get_volume_cgroups_data(self):
        try:
            return []
        except Exception:
            cgroups = []
            exceptions.handle(self.request, _("Unable to retrieve "
                                              "volume consistency groups."))
        return cgroups


class VolumeAndSnapshotTabs(tabs.TabGroup):
    slug = "volumes_and_snapshots"
    tabs = (VolumeTab, CGroupsTab)
    sticky = True
