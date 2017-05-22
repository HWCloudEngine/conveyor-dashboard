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

  horizon.modals.addModalInitFunction(conveyorClonePlan);
  horizon.modals.addModalInitFunction(conveyorCloneDestination);

  function conveyorClonePlan(modal) {
    var clonePlanForm = $(modal).find('#clone_plan_form');
    var plan_id = $(clonePlanForm).find('[name=plan_id]').val();
    $(modal).find('.modal-footer a.cancel_plan').click(function () {
      console.log('cancel clone plan: ' + plan_id);
      $.ajaxSetup({async: false});
      $.ajaxSetup({beforeSend: function(xhr, settings){xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));}});
      $.post(WEBROOT + "/conveyor/plans/" + plan_id + "/cancel", function(json){});
    });
    // $(modal).find('a.close').click(window.conveyor.cancel_clone);
    // $(modal).find('.modal-footer .btn-clone').click(function () {
    //   $.ajaxSetup({beforeSend: function(xhr, settings){xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));}});
    //   $.post(
    //     WEBROOT + '/conveyor/plans/' + plan_id + '/update_resource',
    //     $(modal).serialize(),
    //     function (rsp) {
    //       // TODO(drngsl) if process failed in backend, return False
    //     }
    //   )
    // });
  }

  function conveyorCloneDestination(modal) {
    var destinationForm = $(modal).find('#destination_form');
    var clonePlanForm = $('#clone_plan_form');
    if (clonePlanForm) {
      $(destinationForm).find('.modal-footer [type=submit]').click(function () {
        // $(clonePlanForm).find('#')
        $(clonePlanForm).submit();
      });
    }
  }

  var cloneFormModal = $('#clone_plan_form').parent();
  if (cloneFormModal) {
    conveyorClonePlan(cloneFormModal);
  }

  var destinationFormModal = $('#destination_form').parent();
  if (destinationFormModal) {
    conveyorCloneDestination(destinationFormModal);
  }
});
