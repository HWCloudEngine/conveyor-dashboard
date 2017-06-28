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

from openstack_dashboard.api import base


class Resource(base.APIDictWrapper):
    """Resource wrap for dict resources."""


class Plan(base.APIResourceWrapper):
    _attrs = ['plan_id', 'plan_name', 'plan_type', 'plan_status',
              'task_status', 'user_id', 'project_id', 'clone_obj',
              'created_at', 'updated_at']

    @property
    def id(self):
        return self.plan_id


class OverviewResource(base.APIDictWrapper):
    _attrs = ['res_id', 'res_type', 'name', 'tenant_id', 'availability_zone']

    @property
    def id(self):
        return self.res_id

    def project_id(self):
        try:
            return self.tenant_id
        except (KeyError, AttributeError):
            return '-'


class Volume(base.APIResourceWrapper):

    _attrs = ['id', 'name', 'description', 'size', 'status', 'created_at',
              'volume_type', 'availability_zone', 'imageRef', 'bootable',
              'snapshot_id', 'source_volid', 'attachments', 'tenant_name',
              'consistencygroup_id', 'os-vol-host-attr:host',
              'os-vol-tenant-attr:tenant_id', 'metadata',
              'volume_image_metadata', 'encrypted', 'transfer']

    @property
    def is_bootable(self):
        return self.bootable == 'true'

    @property
    def name(self):
        # If a volume doesn't have a name, use its id.
        return (getattr(self._apiresource, 'name', None) or
                getattr(self._apiresource, 'display_name', None) or
                getattr(self._apiresource, 'id', None))

    @property
    def description(self):
        return (getattr(self._apiresource, 'description', None) or
                getattr(self._apiresource, 'display_description', None))


class Stack(base.APIResourceWrapper):
    _attrs = ['id', 'stack_name', 'creation_time', 'updated_time',
              'stack_status']

    @property
    def status(self):
        # If a volume doesn't have a name, use its id.
        s = getattr(self._apiresource, 'task_status')
        return s[s.index('_') + 1:]
