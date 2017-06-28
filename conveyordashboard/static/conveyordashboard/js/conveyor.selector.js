/*  Copyright (c) 2017 Huawei, Inc.

 Licensed under the Apache License, Version 2.0 (the "License"); you may
 not use this file except in compliance with the License. You may obtain
 a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 License for the specific language governing permissions and limitations
 under the License.
 */

$(function () {
  "use strict";

  var create_plan_tag = 'a.create-plan-with-multi-res';
  var res_ids = {};

  function get_table_res_type(table) {
    var classes = $(table).attr("class").split(" ");
    for (var index = 0; index < classes.length; index++) {
      var css_class = classes[index];
      if (css_class.startsWith("OS::")) {
        return css_class;
      }
    }
    return "";
  }

  function check_topology_link() {
    if ($(create_plan_tag).length === 0) {
      return;
    }
    var len = 0;
    $.each(res_ids, function (k, v) {
      len += v.length;
    });
    if (len > 0) {
      if ($(create_plan_tag).hasClass("disabled")) {
        $(create_plan_tag).removeClass("disabled");
      }
    } else {
      if (!$(create_plan_tag).hasClass("disabled")) {
        $(create_plan_tag).addClass("disabled");
      }
    }
  }

  function get_query_string() {
    var id_strs = [];
    $.each(res_ids, function (k, v) {
      if (v.length > 0) {
        id_strs.push(k + "*" + v.join(","));
      }
    });
    return "?ids=" + id_strs.join("**");
  }

  var create_plan = function () {
    var href = $(this).attr("href").split("?")[0];
    href += get_query_string();
    $(this).attr("href", href);
    return true;
  };

  $(function () {
    if ($(create_plan_tag).length) {
      $(create_plan_tag).click(create_plan);

      $("table.table-res").each(function () {
        var type = get_table_res_type(this);
        var this_table = this;
        $(this).find("thead input.table-row-multi-select").click(function () {
          if ($(this).attr("checked") == "checked") {
            var tmp_res_ids = [];
            $(this_table).find("tbody tr").each(function () {
              res_ids.push($(this).find("input[type=checkbox][name=object_ids]")[0].value);
            });
            res_ids[type] = tmp_res_ids;
          } else {
            res_ids[type] = [];
          }
          check_topology_link();
        });
        $(this).find("tbody tr").each(function () {
          var tr = this;
          $(this).find("input.table-row-multi-select").click(function () {
            var uuid = $(this).val();
            var tmp_res_ids = [];
            if (res_ids.hasOwnProperty(type)) {
              tmp_res_ids = res_ids[type];
            }
            if ($(this).attr("checked") == "checked") {
              if ($.inArray(uuid, tmp_res_ids) === -1) {
                tmp_res_ids.push(uuid)
              }
            } else {
              var index = $.inArray(uuid, tmp_res_ids);
              if (index !== -1) {
                tmp_res_ids.splice(index, 1)
              }
            }
            res_ids[type] = tmp_res_ids;
            check_topology_link();
          });
        });
      });
    }
  });
});