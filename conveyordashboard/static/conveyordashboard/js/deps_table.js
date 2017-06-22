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

var depsTreeTableAndCallTopo = function () {
  var plan_deps_table = $('#plan_deps_table');
  if (plan_deps_table.length) {
    /* Redraw the global topology.*/
    $(plan_deps_table).find('#plan_deps__action_global_topology').click(function () {
      try {
        redraw($(this).attr('href'));
        return false
      } catch (e) {
        console.error("Redraw failed: " + e);
        return false;
      }
    });
    var resource_type = [];
    $(plan_deps_table).find('tbody tr').each(function () {
      /* Click one resource of plan, then redraw the local topology.*/
      $(this).find('td:last a').click(function () {
        try {
          redraw($(this).attr('href'));
          return false
        } catch (e) {
          console.error("Redraw failed: " + e);
          return false;
        }
      });
      var type = $(this).find('td:eq(3)').html();
      if (resource_type.toString().indexOf(type) == -1) {
        resource_type.push(type);
      }
    });
    for (var i = 0; i < resource_type.length; i++) {
      $(plan_deps_table).find('tbody').prepend("<tr id='node--2-" + (i + 1) + "' class='parent'><td colspan='5'>" + resource_type[i] + "</td></tr>");
      $(plan_deps_table).find('tbody tr').each(function () {
        if ($(this).find('td:eq(3)').html() == resource_type[i]) {
          $(this).addClass("child-of-node--2-" + (i + 1));
          $(plan_deps_table).find('tbody tr#node--2-' + (i + 1)).after($(this));
        }
      });
    }
    $("#plan_deps").treeTable();
    $(plan_deps_table).css({'display': 'block'});
  }
};
