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

"use strict";

var conveyorService = {
  cancelPlan: function (plan_id) {
    $.ajaxSetup({beforeSend: function(xhr, settings){xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));}});
    $.post(WEBROOT + "api/conveyor/plans/" + plan_id + "/delete/")
      .error(function () {
        horizon.alert('error', gettext("Unable to cancel plan Cancel Plan."));
      });
  },

  updatePlanResourceForFrontend: function (plan_id, data) {
    var result = null;
    $.ajaxSetup({async: false});
    $.ajaxSetup({beforeSend: function(xhr, settings){xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));}});
    $.post(WEBROOT + 'api/conveyor/plans/' + plan_id + '/update_plan_resource_frontend/', angular.toJson(data))
      .success(function (data) {
        result = data;
      })
      .error(function () {
        horizon.alert('error', gettext("Unable to update plan resource."));
        result = false;
      });
    return result;
  },

  getResourceDetail: function (data) {
    var result = null;
    $.ajaxSetup({async: false});
    $.ajaxSetup({beforeSend: function(xhr, settings){xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));}});
    $.post(WEBROOT + 'api/conveyor/plans/' + data.plan_id + '/detail_resource/' + data.resource_id + '/', angular.toJson(data))
      .success(function (data) {
        result = data;
      })
      .error(function () {
        horizon.alert('error', gettext('Unable to retrieve resource detail.'));
      });
    return result;
  },

  addRuleForFrontend: function (sg_id, data) {
    var result = null;
    $.ajaxSetup({async: false});
    $.get(WEBROOT + '/conveyor/security_groups/add_rule/?security_group_id=' + sg_id)
      .success(function (data) {
        result = data;
      });
    return result;
  },

  createSGRule: function (sg_id, data) {
    var result = null;
    $.ajaxSetup({async: false});
    $.ajaxSetup({beforeSend: function(xhr, settings){xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));}});
    $.post(WEBROOT + 'api/conveyor/resources/create_rule/', angular.toJson(data))
      .success(function (data) {
        result = data;
      })
      .error(function () {
      horizon.alert('error', gettext('Unable to create security group rule.'));
    });
    return result;
  }
};
