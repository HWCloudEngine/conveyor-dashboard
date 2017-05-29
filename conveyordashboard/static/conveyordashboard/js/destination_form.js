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

  horizon.modals.addModalInitFunction(conveyorPlanDestination);

  function conveyorPlanDestination(modal) {
    var destinationForm = $(modal).find('#destination_form');
    var migratePlanForm = $('#migrate_plan_form');
    var updateResourcesField = $('[name=update_resource]');
    if (updateResourcesField.length && !migratePlanForm.length) {
      $(destinationForm).find('[name=resources]').val($(updateResourcesField).val());
    }
  }

  var destinationFormModal = $('#destination_form').parent();
  if (destinationFormModal.length) {
    conveyorPlanDestination(destinationFormModal);
  }
});
