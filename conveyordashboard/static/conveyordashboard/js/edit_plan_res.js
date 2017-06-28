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

function loadGlobalTopo(planId) {
  conveyorPlanTopology.updateTopo(conveyorPlan.globalDependencies(planId));
  if($('#id_plan_type').val() == 'clone'){$('g.node[cloned=false]').unbind('click').bind('click', function () {
    conveyorEditPlanRes.nodeClick(this);
  });}
  return false;
}

function loadLocalTopo(planId, resType, resId) {
  conveyorPlanTopology.updateTopo(conveyorPlan.localDependencies(planId, resType, resId));
  if($('#id_plan_type').val() == 'clone'){$('g.node[cloned=false]').unbind('click').bind('click', function () {
    conveyorEditPlanRes.nodeClick(this);
  });}
  return false;
}

var conveyorEditPlanRes = {
  /* Tag for HTML element */
  tag_detailinfo_div: "div.detailInfoCon",
  tag_update_resource: "input#id_update_resource",
  tag_updated_resources: "input#id_updated_resources",
  tag_dependencies: "input#id_dependencies",
  tag_plan_id: "input#id_plan_id",
  /* properties */
  isUpdating: false,
  nodeClick: function (node) {
    var self = this;
    this.clearEditing();
    var node_id = $(node).attr("node_id");
    var node_type = $(node).attr("node_type");
    var plan_id = $(this.tag_plan_id).val();

    // Get resource from server
    var resView = conveyorService.getResourceView(plan_id, conveyorPlan.extractResourceShowInfo(plan_id, node_type, node_id));

    if(! resView) {
      return false;
    }
    $("image#" + node_id).attr("href", resView.image);
    var click_img = resView.image;
    if(click_img != "") {
      var img_node = $("image[id=image_" + node_id.replace(/\./g, '__') + "]");
      img_node.attr("ori-href", img_node.attr("href"));
      img_node.attr({"href": click_img, "editing": true});
    }

    // Show view
    self.popResEditModal(node_type, node_id, resView.data);
    $("select[name='networks'],select[name='routers'],select[name='subnets'],select[name='secgroups'],select[name='volumetypes']").parent().parent().css({
        'display':'none'
    });

    $("#id_from_other").parent().click(function(){
        if($("#id_from_other").is(':checked')){
            $("select[name='networks'],select[name='routers'],select[name='subnets'],select[name='secgroups'],select[name='volumetypes']").parent().parent().css({
                'display':'block'
            });
        }else{
            $("select[name='networks'],select[name='routers'],select[name='subnets'],select[name='secgroups'],select[name='volumetypes']").parent().parent().css({
                'display':'none'
            });
        }
    });
  },
  clearEditing: function () {
    $("image[editing=true]").each(function(){
      $(this).attr({"href": $(this).attr("ori-href"), "editing": false});
    });
  },

  saveTableInfo: function () {
    var self = this;
    try {
      if(self.isUpdating){return false;}
      self.isUpdating = true;
      var planId = $(self.tag_plan_id).val();
      var resource_type = $(self.tag_detailinfo_div).attr("resource_type");
      var resource_id = $(self.tag_detailinfo_div).attr("resource_id");
      var result = conveyorResources.process(resource_type, resource_id);
      var data = result.data;
      if(Object.keys(data).length){
        conveyorPlan.updatePlanResource(planId, resource_type, resource_id, result);
        if(result.needPosted) {
          conveyorPlanTopology.updateTopo(conveyorPlan.getPlan(planId).updated_deps);
          $('g.node[cloned=false]').unbind('click').bind('click', function () {
            conveyorEditPlanRes.nodeClick(this);
          });
        }
      }
      self.clearEditing();
      $("#conveyor_plan_topology").show();
      $("#thumbnail").show();
      $("#info_box").show().css({"display": "block"});
      $("#stack_box").show().css({"display": "block"});
      return false;
    } catch(err){
      console.log(err);
      return false;
    } finally{
      self.isUpdating = false;
    }
  },
  updatePlanDeps: function(planDeps) {
    var self = this;
    var plan_deps_table = $(planDeps).find('#plan_deps');
    var deps_types = [];
    $(plan_deps_table).find('tbody tr').each(function () {
      var type=$(this).find('td:eq(3)').html();
      if(deps_types.toString().indexOf(type)==-1){
        deps_types.push(type);
      }
    });
    for(var i=0;i<deps_types.length;i++){
      $(plan_deps_table).find('tbody').prepend("<tr id='node--2-"+(i+1)+"' class='parent'><td colspan='5'>"+deps_types[i]+"</td></tr>");
      $(plan_deps_table).find('tbody tr').each(function (){
        if($(this).find('td:eq(3)').html()==deps_types[i]){
          $(this).addClass("child-of-node--2-"+(i+1));
          $(plan_deps_table).find('tbody tr#node--2-'+(i+1)).after($(this));
        }
      });
    }
    $("#plan_deps").find('tbody').html($(plan_deps_table).find('tbody').html());
    // self.configLocalTopology();
  },
  /* For resource detail. Allow to add some items for property with type of list
   * of detail resource.
   * params:
   * seletor: 			js selector of the table being to operate.
   * type: 				the type (or name) of table. like: metadatas, rules
   * addActionSelector: js selector of the add action button.*/
  openAddOperation: function (seletor, type, addActionSelector) {
    var self = this;
    if($(addActionSelector).length){
      $(addActionSelector).click(function(){
        if(type == "rules"){
          if($("form#create_security_group_rule_form").length){
            return;
          }
          var rsp = conveyorService.addRuleForFrontend($('#secgroup_wrap').attr('os_id'));
          conveyorEditPlanRes.popAddRuleModalForm(rsp, 'create_security_group_rule_form', conveyorEditPlanRes.addSGRuleForSG);
          return false;
        }
      });
    }
  },
  popAddRuleModalForm: function (formHtml, formId, submitCall) {
    var form = $(formHtml).find('form#' + formId);
    var content =  $(form).parent();
    var title = $(content).find('.modal-header .modal-title').text();
    var submitLabel = $(content).find('.modal-footer [type=submit]').val();
    var modal = horizon.modals.create(title, '', submitLabel);
    $(modal).find('.modal-body')
      .html($(form).find('.modal-body').prop("innerHTML"));
    $(modal).find('.modal-footer .btn-primary').click(function () {
      submitCall();
      $(modal).modal('hide');
    });
    $(modal).modal();
    $("#id_rule_menu").trigger('change', $("#id_rule_menu").children().eq(1));
  },
  /* For resource detail. All to delete some items for property with type of list
   * of detail resource.
   * params:
   * seletor:			js selector of the table being to operate.
   * delActionSelector: js selector of the delete action button.*/
  openDeleteOperation: function (seletor, delActionSelector) {
    if($(delActionSelector).length){
      $(delActionSelector).click(function(){
        conveyorEditPlanRes.removeTableItems(seletor, delActionSelector);return false;
      });
    }
    $(seletor).find("thead input.table-row-multi-select").click(function(){
      if ($(this).attr("checked") == "checked") {
        if($(delActionSelector).hasClass("disabled")){$(delActionSelector).removeClass("disabled");}
      } else {
        if(!$(delActionSelector).hasClass("disabled")){$(delActionSelector).addClass("disabled");}
      }
    });
    $(seletor).find("tbody input.table-row-multi-select").click(function(){
      if($(seletor).find("tbody input.table-row-multi-select").length){
        if($(delActionSelector).hasClass("disabled")){
          $(delActionSelector).removeClass("disabled");
        }
      }else{
        if(!$(delActionSelector).hasClass("disabled")){
          $(delActionSelector).addClass("disabled");
        }
      }
    });
  },
  /* Remove items for table temporary. while not delete behind
   * params:
   * selector:			the css selector of the table being to operate.
   * delActionSelector: js selector of the delete action button.*/
  removeTableItems: function (selector, delActionSelector) {
    $(selector).find("tbody tr").each(function(){
      if($(this).find("input[name=object_ids].table-row-multi-select").attr("checked")=="checked"){
        var item_id = $(this).attr("data-object-id");
        if(typeof($(selector).attr("deleted_ids"))=="undefined"){$(selector).attr("deleted_ids", item_id);}
        else{$(selector).attr("deleted_ids", $(selector).attr("deleted_ids") + " " + item_id);}
        $(this).remove();
      }
    });
    if(!$(delActionSelector).hasClass("disabled")){$(delActionSelector).addClass("disabled");}
  },
  addSGRuleForSG: function () {
    var secgroup_rule = {
      'rule_menu': $("select#id_rule_menu").val(),
      'direction': $("select#id_direction").val(),
      'ip_protocol': $("#id_ip_protocol").val(),
      'port_or_range': $("#id_port_or_range").val(),
      'port': parseInt($("#id_port").val()),
      'from_port': parseInt($("#id_from_port").val()),
      'to_port': parseInt($("#id_to_port").val()),
      'icmp_type': $("#id_icmp_type").val(),
      'icmp_code': $("#id_icmp_code").val(),
      'remote': $("#id_remote").val(),
      'cidr': $("#id_cidr").val(),
      'security_group': $("#id_security_group").val(),
      'ethertype': $("#id_ethertype").val()
    };

    var result = conveyorService.createSGRule($("#secgroup_wrap").attr('od_id'), secgroup_rule);
    if(result) {
       var sgr = result.sgr;
        var sgrs_node = $("#id_sgrs");
        var ori_rs = $.parseJSON($(sgrs_node).attr("data-ori"));
        ori_rs.push(sgr);
        $(sgrs_node).attr({"data-ori": JSON.stringify(ori_rs), "changed": true});
        $("table#rules tbody").append($(result.sgr_html).find("tbody tr").prop("outerHTML"));
        conveyorEditPlanRes.openDeleteOperation('form table#rules', '#rules__action_delete_rule');
    }
    return false;
  },
  popResEditModal: function (resType, resId, data) {
    conveyorResources.prefixCss = '.modal.edit-plan-res';
    var modal = horizon.modals.create(gettext('Edit Plan Resource:') + gettext(resType.split('::')[2]), '', gettext('Save'));
    $(modal)
      .addClass('edit-plan-res')
      .find('.modal-body')
      .html(data);
    $(modal).find('.modal-footer .btn-primary').click(function () {
      conveyorEditPlanRes.saveTableInfo();
      $(modal).modal('hide');
    });
    $(modal).modal();
  }
};
