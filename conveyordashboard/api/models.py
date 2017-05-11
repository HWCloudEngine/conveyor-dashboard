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


class Server(base.APIDictWrapper):
    _attrs = ['addresses', 'attrs', 'id', 'image', 'links', 'metadata', 'name',
              'private_ip', 'public_ip', 'status', 'uuid', 'image_name',
              'VirtualInterfaces', 'flavor', 'key_name', 'fault', 'tenant_id',
              'user_id', 'created', 'OS-EXT-STS:power_state',
              'OS-EXT-STS:task_state', 'OS-EXT-SRV-ATTR:instance_name',
              'OS-EXT-SRV-ATTR:host', 'OS-EXT-AZ:availability_zone',
              'OS-DCF:diskConfig']


class Flavor(base.APIDictWrapper):
    _attrs = ['ram', 'vcpus', 'disk', 'swap', 'ephemeral', 'rxtx_factor',
              'extra_specs', 'is_public']


class Metadata(base.APIDictWrapper):
    _attrs = ['id', 'key', 'value']

    @property
    def id(self):
        return self.key


class Volume(base.APIDictWrapper):

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
        return self.display_name

    @property
    def description(self):
        return self.display_description


class Stack(base.APIDictWrapper):

    _attrs = ['id', 'stack_name', 'creation_time', 'updated_time',
              'stack_status']

    # @property
    # def action(self):
    #     s = self.stack_status
    #     # Return everything before the first underscore
    #     return s[:s.index('_')]

    @property
    def status(self):
        s = self.stack_status
        # Return everything after the first underscore
        return s[s.index('_') + 1:]

    # @property
    # def identifier(self):
    #     return '%s/%s' % (self.stack_name, self.id)


class StackRes(base.APIResourceWrapper):
    _attrs = ['id', 'stack_name', 'creation_time', 'updated_time',
              'stack_status']

    @property
    def status(self):
        # If a volume doesn't have a name, use its id.
        s = getattr(self._apiresource, 'task_status')
        return s[s.index('_') + 1:]
