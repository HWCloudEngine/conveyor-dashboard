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
    $.post(WEBROOT + "/conveyor/plans/" + plan_id + "/cancel")
      .error(function () {
        horizon.alert('error', gettext("Cancel Plan " + plan_id + " failed"));
      });
  },

  updatePlanResourceForFrontend: function (plan_id, data) {
    var result = null;
    $.ajaxSetup({async: false});
    $.ajaxSetup({beforeSend: function(xhr, settings){xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));}});
    $.post(WEBROOT + '/conveyor/plans/' + plan_id + '/update_plan_resource', data)
      .success(function (data) {
        result = data;
      })
      .error(function () {
        horizon.alert('error', gettext("Update plan resource failed"));
        result = false;
      });
    return result;
  },

  getResourceDetail: function (data) {
    var result = null;
    $.ajaxSetup({async: false});
    $.ajaxSetup({beforeSend: function(xhr, settings){xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));}});
    $.post(WEBROOT + '/conveyor/plans/get_resource_detail', data)
      .success(function (data) {
        result = data;
      })
      .error(function () {
        horizon.alert('error', gettext('Get detail resource failed'));
      });
    return result;
  },

  addRuleForFrontend: function (sg_id, data) {
    var result = null;
    $.ajaxSetup({async: false});
    $.get(WEBROOT + '/conveyor/plans/secgroup/add_rule/?security_group_id=' + sg_id)
      .success(function (data) {
        result = data;
      });
    return result;
  },

  createSGRule: function (sg_id, data) {
    var result = null;
    $.ajaxSetup({async: false});
    $.ajaxSetup({beforeSend: function(xhr, settings){xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));}});
    $.post(WEBROOT + '/conveyor/plans/secgroup/create_rule/', data)
      .success(function (data) {
        result = data;
      })
      .error(function () {
      horizon.alert('error', gettext('Create security group rule failed.'));
    });
    return result;
  }
};
