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

IMAGE_DIR = 'conveyordashboard/img/'

NOVA_SERVER = 'OS::Nova::Server'
NOVA_KEYPAIR = 'OS::Nova::KeyPair'
NOVA_FLAVOR = 'OS::Nova::Flavor'
NOVA_AZ = 'OS::Nova::AvailabilityZone'
CINDER_VOLUME = 'OS::Cinder::Volume'
CINDER_VOL_TYPE = 'OS::Cinder::VolumeType'
CINDER_QOS = 'OS::Cinder::Qos'
CINDER_CONSISGROUP = 'OS::Cinder::ConsisGroup'
NEUTRON_NET = 'OS::Neutron::Net'
NEUTRON_SUBNET = 'OS::Neutron::Subnet'
NEUTRON_PORT = 'OS::Neutron::Port'
NEUTRON_ROUTER = 'OS::Neutron::Router'
NEUTRON_SECGROUP = 'OS::Neutron::SecurityGroup'
NEUTRON_ROUTER_IF = 'OS::Neutron::RouterInterface'
NEUTRON_FLOATINGIP = 'OS::Neutron::FloatingIP'
NEUTRON_FIP_ASSO = 'OS::Neutron::FloatingIPAssociation'
NEUTRON_VIP = 'OS::Neutron::Vip'
NEUTRON_LISTENER = 'OS::Neutron::Listener'
NEUTRON_POOL = 'OS::Neutron::Pool'
NEUTRON_POOLMEMBER = 'OS::Neutron::PoolMember'
NEUTRON_HEALTHMONITOR = 'OS::Neutron::HealthMonitor'
GLANCE_IMAGE = 'OS::Glance::Image'
HEAT_STACK = 'OS::Heat::Stack'

TAG_RES_TYPE = 'resource_type'
TAG_RES_ID = 'resource_id'
TAG_FROM = 'from'
TAG_FROM_ID = 'res_id_from'
TAG_UPDATED = 'res_updated'

RES_ACTION_KEY = 'action'
RES_ACTIONS = (ACTION_EDIT, ACTION_DELETE, ACTION_ADD) \
    = ('edit', 'delete', 'add')


PLAN_TYPE = (MIGRATE, CLONE) = ('migrate', 'clone')

DEPENDENCY_UPDATE_MAPPING = {
    NEUTRON_NET: [NEUTRON_SUBNET],
    NEUTRON_SUBNET: [NEUTRON_PORT],
    CINDER_VOLUME: [CINDER_VOL_TYPE],
    CINDER_VOL_TYPE: [CINDER_QOS],
}

RESOURCE_TYPE_IMAGE_MAPPINGS = {
    # Nova
    NOVA_SERVER: {
        'green': 'server-green.svg',
        'red': 'server-red.svg',
        'gray': 'server-gray.svg'
    },
    NOVA_KEYPAIR: {
        'green': 'keypair-green.svg',
        'red': 'keypair-red.svg',
        'gray': 'keypair-gray.svg'
    },
    NOVA_FLAVOR: {
        'green': 'flavor-green.svg',
        'red': 'flavor-red.svg',
        'gray': 'flavor-red.svg'
    },
    # Cinder
    CINDER_VOLUME: {
        'green': 'volume-green.svg',
        'red': 'volume-red.svg',
        'gray': 'volume-gray.svg'
    },
    CINDER_VOL_TYPE: {
        'green': 'volumetype-green.svg',
        'red': 'volumetype-red.svg',
        'gray': 'volumetype-gray.svg'
    },
    CINDER_QOS: {
        'green': 'qos-green.svg',
        'red': 'qos-red.svg',
        'gray': 'qos-gray.svg'
    },
    CINDER_CONSISGROUP: {
        'green': 'consisgroup-green.svg',
        'red': 'consisgroup-red.svg',
        'gray': 'consisgroup-gray.svg'
    },
    # Neutron
    NEUTRON_NET: {
        'green': 'net-green.svg',
        'red': 'net-red.svg',
        'gray': 'net-gray'
    },
    NEUTRON_SUBNET: {
        'green': 'subnet-green.svg',
        'red': 'subnet-red.svg',
        'gray': 'subnet-gray.svg'
    },
    NEUTRON_ROUTER: {
        'green': 'router-green.svg',
        'red': 'router-red.svg',
        'gray': 'router-gray.svg'
    },
    NEUTRON_SECGROUP: {
        'green': 'securitygroup-green.svg',
        'red': 'securitygroup-red.svg',
        'gray': 'securitygroup-gray.svg'
    },
    NEUTRON_PORT: {
        'green': 'port-green.svg',
        'red': 'port-red.svg',
        'gray': 'port-gray.svg'
    },
    NEUTRON_ROUTER_IF: {
        'green': 'routerinterface-green.svg',
        'red': 'routerinterface-red.svg',
        'gray': 'routerinterface-gray.svg'
    },
    NEUTRON_FLOATINGIP: {
        'green': 'floatingip-green.svg',
        'red': 'floatingip-red.svg',
        'gray': 'floatingip-gray.svg'
    },
    NEUTRON_FIP_ASSO: {
        'green': 'floatingipassociation-green.svg',
        'red': 'floatingipassociation-red.svg',
        'gray': 'floatingipassociation-gray.svg'
    },
    NEUTRON_VIP: {
        'green': 'vip-green.svg',
        'red': 'vip-red.svg',
        'gray': 'vip-gray.svg'
    },
    NEUTRON_LISTENER: {
        'green': 'listener-green.svg',
        'red': 'listener-red.svg',
        'gray': 'listener-gray.svg'
    },
    NEUTRON_POOL: {
        'green': 'pool-green.svg',
        'red': 'pool-red.svg',
        'gray': 'pool-gray.svg'
    },
    NEUTRON_POOLMEMBER: {
        'green': 'poolmember-green.svg',
        'red': 'poolmember-red.svg',
        'gray': 'poolmember-gray.svg'
    },
    NEUTRON_HEALTHMONITOR: {
        'green': 'healthmonitor-green.svg',
        'red': 'healthmonitor-red.svg',
        'gray': 'healthmonitor-gray.svg'
    },
    # Stack
    HEAT_STACK: {
        'green': 'stack-green.svg',
        'red': 'stack-red.svg',
        'gray': 'stack-gray.svg'
    },
    # Unknown type
    'UNKNOWN': {
        'green': 'unknown.svg',
        'red': 'unknown-red.svg',
        'gray': 'unknown-gray.svg'
    },
}
