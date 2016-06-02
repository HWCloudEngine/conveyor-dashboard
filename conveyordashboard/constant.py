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

RESOURCE_TYPE = 'type'
RESOURCE_ID = 'res_id'
IMAGE_DIR = 'conveyordashboard/img/'

resource_type = ['OS::Nova::Server',
                 'OS::Cinder::Volume',
                 'OS::Neutron::Net',
                 'OS::Neutron::Router',
                 'OS::Neutron::LoadBalancer',
                 'OS::Heat::Stack']

TAG_RES_TYPE = "type"
TAG_RES_ID = "res_id"
TAG_FROM = "from"
TAG_FROM_ID = "res_id_from"
TAG_UPDATED = "res_updated"

DEPENDENCY_UPDATE_MAPPING = {
    "OS::Neutron::Net": ["OS::Neutron::Port", "OS::Neutron::Subnet"],
    "OS::Neutron::Subnet": ["OS::Neutron::Port", "OS::Neutron::Net"],
}

RESOURCE_TYPE_IMAGE_MAPPINGS = {
    #nova
    'OS::Nova::Server':     {'green': 'server-green.svg',
                             'red': 'server-red.svg'},
    'OS::Nova::KeyPair':    {'green': 'keypair-green.svg',
                             'red':'keypair-red.svg'},
    'OS::Nova::Flavor':     {'green': 'flavor-green.svg',
                             'red': 'flavor-red.svg'},
    #volume
    'OS::Cinder::Volume':   {'green': 'volume-green.svg',
                             'red':'volume-red.svg'},
    'OS::Cinder::VolumeType':   {'green': 'volumetype-green.png',
                             'red':'volumetype-red.png'},
    #neutron
    'OS::Neutron::Net':     {'green': 'network-green.svg',
                             'red': 'network-red.svg'},
    'OS::Neutron::Subnet':  {'green': 'subnet-green.png',
                             'red': 'subnet-red.png'},
    'OS::Neutron::Router':  {'green': 'router-green.svg',
                             'red':'router-red.svg'},
    'OS::Neutron::SecurityGroup': {'green': 'securitygroup-green.svg',
                                   'red': 'securitygroup-red.svg'},
    'OS::Neutron::Port':    {'green':'port-green.svg',
                             'red':'port-red.svg'},
    'OS::Neutron::RouterInterface':    {'green':'routerinterface-green.png',
                             'red':'routerinterface-red.png'},
    'OS::Neutron::FloatingIP':    {'green':'floatingip-green.svg',
                             'red':'floatingip-red.svg'},
    #unknown type
    'UNKNOWN':    {'green':'unknown.svg',
                             'red':'unknown-red.svg'},
    }
