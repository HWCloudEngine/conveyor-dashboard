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
      deletePlan: deletePlan,
      editPlanResource: editPlanResource,
    };

    return service;

    function deletePlan(plan_id) {
      return apiService.get('/api/conveyor/plans/' + plan_id + '/cancel/')
        .error(function() {
          toastService.add('error', gettext('Unable to delete plan.'));
        });
    }
    function editPlanResource(plan_id, res_type, res_id, updata_data) {
      return apiService.post('/api/conveyor/plans' + plan_id + '/' + res_type + '/' + res_id, updata_data)
        .error(function () {
          toastService.add('error', gettext('Unable to update plan resource.'))
        });
    }
  }
}());