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

  horizon.modals.addModalInitFunction(conveyorMigratePlan);

  function conveyorMigratePlan(modal) {
    var migratePlanForm = $(modal).find('#migrate_plan_form');
    var plan_id = $(migratePlanForm).find('[name=plan_id]').val();
    $(modal).find('.modal-footer a.cancel_migrate').click(function () {
      conveyorService.cancelPlan(plan_id);
    });
    $(modal).find('.modal-header a.close').click(function () {
      conveyorService.cancelPlan(plan_id)
    });
  }

  conveyorMigratePlan($('#migrate_plan_form').parent());
});
