/*
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

(function () {
  'use strict';

  /**
   * @ngdoc module
   * @ngname horizon.app.conveyor
   * @description
   * Dashboard module to host conveyor panels.
   */
  angular
    .module('horizon.app.conveyor', [
      'horizon.app.conveyor.overview_az',
    ])
    .constant('horizon.app.conveyor.resourceTypes', {
      NOVA_SERVER: 'OS::Nova::Server',
      NOVA_KEYPAIR: 'OS::Nova::KeyPair',
      NOVA_FLAVOR: 'OS::Nova::Flavor',
      NOVA_AZ: 'OS::Nova::AvailabilityZone',
      CINDER_VOLUME: 'OS::Cinder::Volume',
      CINDER_VOL_TYPE: 'OS::Cinder::VolumeType',
      CINDER_QOS: 'OS::Cinder::Qos',
      CINDER_CONSISGROUP: 'OS::Cinder::ConsisGroup',
      NEUTRON_NET: 'OS::Neutron::Net',
      NEUTRON_SUBNET: 'OS::Neutron::Subnet',
      NEUTRON_PORT: 'OS::Neutron::Port',
      NEUTRON_ROUTER: 'OS::Neutron::Router',
      NEUTRON_SECGROUP: 'OS::Neutron::SecurityGroup',
      NEUTRON_ROUTER_IF: 'OS::Neutron::RouterInterface',
      NEUTRON_FLOATINGIP: 'OS::Neutron::FloatingIP',
      NEUTRON_FIP_ASSO: 'OS::Neutron::FloatingIPAssociation',
      NEUTRON_VIP: 'OS::Neutron::Vip',
      NEUTRON_LISTENER: 'OS::Neutron::Listener',
      NEUTRON_POOL: 'OS::Neutron::Pool',
      NEUTRON_POOLMEMBER: 'OS::Neutron::PoolMember',
      NEUTRON_HEALTHMONITOR: 'OS::Neutron::HealthMonitor',
      GLANCE_IMAGE: 'OS::Glance::Image',
      HEAT_STACK: 'OS::Heat::Stack'
    })
    .constant('horizon.app.conveyor.planTypes', {
      CLONE: 'clone',
      MIGRATE: 'migrate'
    })
    .config(config);

  config.$inject = [
    '$provide',
    '$windowProvider'
  ];
  
  function config($provide, $windowProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'dashboard/conveyor/';
    $provide.constant('horizon.app.conveyor.basePath', path);
    var baseRoute = 'conveyor/';
    $provide.constant('horizon.app.conveyor.baseRoute', baseRoute);
  }

})();
