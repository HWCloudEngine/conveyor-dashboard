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
    $(savePlanForm).find('[name=resources]').val($('#id_update_resource').val());
    // TODO(drngsl) On destination page, the 'sys_clone' checkbox does not response to click, here removing the 'themable-checkbox' class to enable it.
    if($('#clone_plan_form').length) {
      var chk_sys_clone = $(savePlanForm).find('[name=sys_clone]');
      if(chk_sys_clone.length) {
        $(chk_sys_clone).parent().removeClass('themable-checkbox');
      }
    }
  }

  var savePlanFormModal = $('#save_plan_form').parent();
  if (savePlanFormModal.length) {
    conveyorSavePlan(savePlanFormModal);
  }
});
