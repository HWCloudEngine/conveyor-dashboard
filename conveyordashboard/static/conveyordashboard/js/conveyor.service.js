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
  syncAjax: function (url, method, data, errorMsg) {
    var result = null;
    $.ajax({
      url: url,
      type: method,
      data: data,
      async: false,
      beforeSend: function (xhr, settings) {
        xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
      },
      success: function (data) {
        result = data;
      },
      error: function (xhr) {
        console.log(xhr);
        if (xhr.status == 401) {
          window.location.href = WEBROOT + 'auth/login/?next=' + window.location.href;
        } else {
          horizon.alert('error', errorMsg);
          result = false;
        }
      }
    });
    return result;
  },

  formatParams: function (params) {
    var result = '';
    $.each(params, function (k, v) {
      if(result != '') {
        result += '&' + k + '=' + v;
      } else {
        result = k + '=' + v;
      }
    });
    return result;
  },

  getResource: function (resType, resId) {
    var result = null;
    var url = WEBROOT + 'api/conveyor/resources/' + resType + '/' + resId + '/';
    $.ajaxSetup({async: false});
    $.get(url)
      .success(function (data) {
        result = data;
      })
      .error(function () {
        horizon.alert('error', gettext('Unable to get detail resource.'));
        result = false;
      });
    return result;
  },

  getResources: function (resType, params) {
    var result = null;
    var url = WEBROOT + 'api/conveyor/resources/' + resType + '/';
    var queryString = this.formatParams(params);
    if (queryString != '') {
      url += '?' + queryString;
    }
    $.ajaxSetup({async: false});
    $.get(url)
      .success(function (data) {
        result = data.items;
      })
      .error(function () {
        horizon.alert('error', gettext('Unable to get detail resource.'));
        result = false;
      });
    return result;
  },

  getResourceView: function (planId, data) {
    return this.syncAjax(
      WEBROOT + 'api/conveyor/plans/' + planId + '/detail_resource/' + data.resource_id + '/',
      'POST',
      angular.toJson(data),
      gettext('Unable to retrieve resource detail.'));
  },

  addRuleForFrontend: function (sg_id, data) {
    var result = null;
    $.ajaxSetup({async: false});
    $.get(WEBROOT + 'conveyor/security_groups/add_rule/?security_group_id=' + sg_id)
      .success(function (data) {
        result = data;
      });
    return result;
  },

  createSGRule: function (sg_id, data) {
    return this.syncAjax(
      WEBROOT + 'api/conveyor/security_groups/create_rule/',
      'POST',
      angular.toJson(data),
      gettext('Unable to create security group rule.'));
  }
};
