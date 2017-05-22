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

$(function () {
  "use strict";

  if (typeof window.conveyor === "undefined") {
    window.conveyor = {};
  }

  if (!window.conveyor.cancel_migrate) {
    window.conveyor.cancel_migrate = function (plan_id) {
      var plan_id = $('#plan_topology_form').find('[name=plan_id]').val();
      $.ajaxSetup({async: false});
      $.ajaxSetup({beforeSend: function(xhr, settings){xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));}});
      $.post(WEBROOT + "/conveyor/plans/" + plan_id + "/cancel", function(json){});
    }
  }

  horizon.modals.addModalInitFunction(conveyorMigratePlan);

  function conveyorMigratePlan(modal) {
    var migratePlanForm = $(modal).find('#plan_topology_form');
    $(modal).find('a.cancel').click(window.conveyor.cancel_migrate);
    $(modal).find('a.close').click(window.conveyor.cancel_migrate);
  }

  conveyorMigratePlan($('#plan_topology_form').parent());
});
