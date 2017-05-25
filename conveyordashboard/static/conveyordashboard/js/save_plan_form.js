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

  horizon.modals.addModalInitFunction(conveyorSavePlan);

  function conveyorSavePlan(modal) {
    var savePlanForm = $(modal).find('#save_plan_form');
    var clonePlanForm = $('#clone_plan_form');
    if(clonePlanForm.length) {
      $(savePlanForm).find('[name=resources]').val($(clonePlanForm).find('[name=update_resource]').val());
    }
  }

  var savePlanFormModal = $('#save_plan_form').parent();
  if (savePlanFormModal.length) {
    conveyorSavePlan(savePlanFormModal);
  }
});
