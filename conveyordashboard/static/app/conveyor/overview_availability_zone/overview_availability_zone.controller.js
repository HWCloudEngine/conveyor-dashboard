/**
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
    .module('horizon.app.conveyor.overview_az')
    .controller('horizon.app.conveyor.overview_az.OverviewAzController', OverviewAzController);

  OverviewAzController.$inject = [
    '$q',
    '$location',
    'horizon.app.core.openstack-service-api.conveyor',
    'horizon.app.conveyor.resourceTypes',
    'horizon.app.conveyor.planTypes',
    'horizon.app.core.openstack-service-api.userSession',
    'horizon.framework.widgets.modal.simple-modal.service'
  ];

  function OverviewAzController($q, $location, conveyor, resourceTypes, planTypes, userSession, simpleModalService) {
    var ctrl = this;
    ctrl.enableBuildTopo = true;
    ctrl.enableClone = false;
    ctrl.projectId = null;
    ctrl.plan = null;
    ctrl.planType = planTypes.CLONE;
    ctrl.availability_zones = [];
    ctrl.src_azs = [];
    ctrl.src_az = null;
    ctrl.dest_azs = [];
    ctrl.dest_az = null;
    ctrl.azMap = {};
    ctrl.incrementalClone = true;
    ctrl.sysClone = false;
    ctrl.copyData = true;

    ctrl.buildTopology = buildTopology;
    ctrl.prepareTopology = prepareTopology;
    ctrl.setEnableExecutePlan = setEnableExecutePlan;
    ctrl.clone = clone;
    
    function buildTopology() {
      if(!ctrl.dest_az || ctrl.dest_az === "") {
        return;
      }

      ctrl.enableBuildTopo = false;
      ctrl.enableClone = false;

      var planName = ctrl.projectId + '#' + ctrl.src_az;
      conveyor.getPlans({plan_name: planName}).then(function (data) {
        var plans = data.data.items;
        angular.forEach(plans, function (p) {
          if ($.inArray(p.plan_status, ['initiating', 'creating', 'available', 'finished', 'cloning', 'migrating']) > -1) {
            ctrl.plan = p;
          }
        });
        if (! ctrl.plan) {
          conveyor.createPlan({
            plan_type: ctrl.planType,
            clone_obj: [{'obj_type': 'availability_zone','obj_id': ctrl.src_az}],
            plan_name: planName
          }).then(function (data) {
            ctrl.plan = data.data;
            ctrl.prepareTopology();
          })
        } else {
          ctrl.prepareTopology();
        }
      }, function () {
        ctrl.plan = null;
        ctrl.enableBuildTopo = true;
      });
    }

    function prepareTopology() {
      // Build plan topology
      conveyorPlanTopology.setLoadding();
      var planId = ctrl.plan.plan_id;
      var azMap = {};
      azMap[ctrl.src_az] = ctrl.dest_az;
      ctrl.azMap = $.extend({}, azMap);
      conveyor.buildResourcesTopo(planId, azMap).then(function (data) {
        var topology = data.data.topo;
        conveyorPlan.initPlan(planId, topology);
        conveyorPlanTopology.loadingFromJson(topology);
        // Set click event for clone plan.
        if (ctrl.plan.plan_type == planTypes.CLONE) {
          $('g.node[cloned=false]').click(function () {
            conveyorEditPlanRes.nodeClick(this);
          })
        }
        ctrl.enableBuildTopo = true;
        ctrl.setEnableExecutePlan();
      }, function () {
        ctrl.enableBuildTopo = true;
        ctrl.enableClone = false;
      })
    }

    function setEnableExecutePlan() {
      if (!ctrl.plan) {
        ctrl.enableClone = false;
        return;
      }

      var planType = ctrl.plan.plan_type;
      var planStatus = ctrl.plan.plan_status;
      if (planType == planTypes.CLONE && $.inArray(planStatus, ['available', 'finished']) > -1) {
        ctrl.enableClone = true;
      }
      return false;
    }

    function clone() {
      var options = {
        title: gettext('Confirm Clone'),
        body: interpolate(
          gettext('Are you sure you want to clone plan %(name)s?'), {name: ctrl.plan.plan_name}, true
          ),
        submit: gettext('Yes'),
        cancel: gettext('No')
      };

      simpleModalService.modal(options).result.then(function confirmed() {
        var planId = ctrl.plan.plan_id;
        var cloneResourceInfo = conveyorPlan.extractCloneInfo(planId, ctrl.incrementalClone);

        conveyor.clone(planId, ctrl.azMap,
          cloneResourceInfo.clone_resources,
          cloneResourceInfo.clone_links,
          cloneResourceInfo.update_resources,
          cloneResourceInfo.replace_resources,
          ctrl.sysClone,
          ctrl.copyData).then(function (data) {
          window.location.href = WEBROOT + 'conveyor/'
        });
      });
    }

    function filterAZ(azs) {
      var result = [];
      angular.forEach(azs, function (az) {
        if (az.zoneName != 'internal') {
          result.push(az);
        }
      });
      return result;
    }
    
    function init() {
      // Check the querystring contain 'availability_zone' or not
      var _zoneName = null;
      var existed = false;

      if ($location.search().availability_zone) {
        _zoneName = $location.search().availability_zone;
      }

      $q.all(
        {
          azs: conveyor.getResources(resourceTypes.NOVA_AZ),
          session: userSession.get()
        }
      ).then(function (d) {
        ctrl.availability_zones = filterAZ(d.azs.data.items);
        ctrl.projectId = d.session.project_id;

        angular.forEach(ctrl.availability_zones, function (az) {
          if (az.zoneName == _zoneName) {
            existed = true;
          }
        });
        ctrl.src_az = existed ? _zoneName : ctrl.availability_zones[0].zoneName;
      });
    }

    init();
  }
}());