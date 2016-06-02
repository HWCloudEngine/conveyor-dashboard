# Copyright 2012 Nebula, Inc.
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


class Server(base.APIDictWrapper):
    _attrs = ['addresses', 'attrs', 'id', 'image', 'links', 'metadata', 'name',
              'private_ip', 'public_ip', 'status', 'uuid', 'image_name',
              'VirtualInterfaces', 'flavor', 'key_name', 'fault', 'tenant_id',
              'user_id', 'created', 'OS-EXT-STS:power_state',
              'OS-EXT-STS:task_state', 'OS-EXT-SRV-ATTR:instance_name',
              'OS-EXT-SRV-ATTR:host', 'OS-EXT-AZ:availability_zone',
              'OS-DCF:diskConfig']


class Flavor(base.APIDictWrapper):
    _attrs = [ 'ram', 'vcpus', 'disk', 'swap', 'ephemeral','rxtx_factor',
              'extra_specs', 'is_public']


class Metadata(base.APIDictWrapper):
    _attrs = ['id', 'key', 'value']

    @property
    def id(self):
        return self.key


class Resource(base.APIDictWrapper):
    """Resource wrap for dict resources."""
