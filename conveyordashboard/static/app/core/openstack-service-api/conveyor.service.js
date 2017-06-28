/**
 * Copyright 2017 Huawei, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

(function () {
  'use strict';

  angular
    .module('horizon.app.core.openstack-service-api')
    .factory('horizon.app.core.openstack-service-api.conveyor', conveyorAPI);

  conveyorAPI.$inject = [
    'horizon.framework.util.http.service',
    'horizon.framework.widgets.toast.service'
  ];

  /**
   * @ngdoc service
   * @name horizon.app.core.openstack-service-api.conveyor
   * @description Provides direct pass through to Conveyor with NO abstraction.
   */

  function conveyorAPI(apiService, toastService) {
    var service = {
      getPlan: getPlan,
      getPlans: getPlans,
      createPlan: createPlan,
      getResources: getResources,
      buildResourcesTopo: buildResourcesTopo,
      clone: clone,
    };

    return service;

    function getPlan(planId) {
      return apiService.get('/api/conveyor/plans/' + planId + '/').error(function () {
        toastService.add('error', gettext('Unable to retrieve plan information.'))
      });
    }
    function getPlans(params) {
      var params = params ? {'params': params} : {};
      return apiService.get('/api/conveyor/plans/', params)
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve plans.'));
        })
    }
    function createPlan(params) {
      return apiService.post('/api/conveyor/plans/', params)
        .error(function () {
          toastService.add('error', gettext('Unable to create plan.'));
        })
    }
    function getResources(resType) {
      return apiService.get('/api/conveyor/resources/' + resType + '/')
        .error(function () {
          toastService.add('error', gettext('Unable to retrieve resource list'));
        })
    }
    function buildResourcesTopo(planId, availabilityZoneMap) {
      var params = {'params': {'availability_zone_map': availabilityZoneMap}};
      return apiService.get('/api/conveyor/plans/' + planId + '/build_resources_topo/', params)
        .error(function () {
          toastService.add('error', gettext('Unable to build resources topology.'))
        })
    }
    function clone(planId, availabilityZoneMap, cloneResources, cloneLinks, updateResources, replaceResources, sysClone, copyData) {
      var params = {
        plan_id: planId,
        availability_zone_map: availabilityZoneMap,
        clone_resources: cloneResources,
        clone_links: cloneLinks,
        update_resources: updateResources,
        replace_resources: replaceResources,
        sys_clone: sysClone,
        copy_data: copyData
      };
      return apiService.post('/api/conveyor/clones/' + planId + '/', params)
        .error(function () {
          toastService.add('error', gettext('Unable to execute to clone plan.'))
        })
    }
  }
}());