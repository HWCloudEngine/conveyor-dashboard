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

from oslo_log import log as logging

from conveyordashboard.common import resource_state

LOG = logging.getLogger(__name__)


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
        try:
            meta = self.table_class._meta
        except AttributeError:
            meta = self.table_classes[0]._meta
        prev_marker = self.request.GET.get(meta.prev_pagination_param, None)
        if prev_marker:
            return prev_marker, "asc"
        else:
            marker = self.request.GET.get(meta.pagination_param, None)
            if marker:
                return marker, "desc"
            return None, "desc"


class FilterTableMixin(object):
    def __init__(self, *args, **kwargs):
        pass

    def _tenant_filter(self, obj):
        tenant_id = obj.get('tenant_id')
        if not tenant_id:
            LOG.error("%s object has no attribute 'tenant_id' ", obj.__class__)
        return tenant_id == self.request.user.tenant_id

    def _instance_status_filter(self, instance):
        return instance.status in resource_state.INSTANCE_CLONE_STATE

    def _volume_status_filter(self, volume):
        return volume.status in resource_state.VOLUME_CLONE_STATE

    def _network_status_filter(self, net):
        status = net.status
        return status in resource_state.NET_CLONE_STATE

    def _pool_status_filter(self, pool):
        return pool.status in resource_state.POOL_CLONE_STATE
