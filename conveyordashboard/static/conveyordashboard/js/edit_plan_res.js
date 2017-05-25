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

var rootPath = getRootPath();

var table_info = "div#resource_info_box";
var detailinfo_div = "div.detailInfoCon";
var update_resources_input = "input#id_update_resource";
var updated_resources_input = "input#id_updated_resources";
var dependencies_input = "input#id_dependencies";

var ipt = "ipt";
var slt = "slt";
var slt_from_existed = "slt_from_existed";
var meta = 'meta';
var res_items = {
	"OS::Nova::Server": {ipt: ["user_data"], meta: ['metadata']},
	"OS::Nova::KeyPair": {slt_from_existed: ["keypairs"]},
	"OS::Cinder::Volume": {ipt: ["name", "size", "description"], slt_from_existed: ['volumes']},
	"OS::Cinder::VolumeType": {slt_from_existed: ["volumetypes"]},
	"OS::Cinder::Qos": {slt_from_existed: ["qoss"]},
	"OS::Neutron::FloatingIP": {slt_from_existed: ["fips"]},
	"OS::Neutron::Router": {ipt: ["name"], slt: ["admin_state_up"], slt_from_existed: ["routers"]},
	"OS::Neutron::PoolMember": {ipt: ["address", "protocol_port","weight"], slt: ["admin_state_up"]},
	"OS::Neutron::Vip": {ipt: ["name", "protocol_port","connection_limit","address"], slt: ["admin_state_up"]},
	"OS::Neutron::Pool": {ipt: ["name", "protocol_port"], slt: ["admin_state_up","lb_method"]},
	"OS::Neutron::HealthMonitor": {ipt: ["delay", "max_retries","timeout"], slt: ["admin_state_up","type"]},
	"OS::Neutron::Listener": {ipt: [ "protocol_port"], slt: ["protocol"]}
};

function redraw(url){
  var deps = '{}';
  if($('input#id_dependencies').length){deps=$('input#id_dependencies').val();}
  var arr = url.split('?');
  var loca = arr[0];
  var param = arr[1];
  var postdata = {"deps": deps,
          "param": param};
  $.ajaxSetup({beforeSend: function(xhr, settings){xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));}});
  jQuery.post(loca, postdata,function(json){
    update_topo(json);
  });
}

function showTopology(){
	$("#resource_info_box").hide();
	$("#conveyor_plan_topology").show();
	$("#thumbnail").show();
}

var conveyorEditPlanRes = {
  /* Tag for HTML element */
  tag_table_info: "div#resource_info_box",
  tag_detailinfo_div: "div.detailInfoCon",
  tag_update_resource: "input#id_update_resource",
  tag_updated_resources: "input#id_updated_resources",
  tag_dependencies: "input#id_dependencies",
  tag_plan_id: "input#id_plan_id",
  tag_is_original: "div#is_original",
  /* properties */
  isUpdating: false,
  nodeClick: function (node) {
    var self = this;
    this.clearEditing();
    var node_id = $(node).attr("node_id");
    var node_type = $(node).attr("node_type");
    var plan_id = $(this.tag_plan_id).val();
    var is_original = $(this.tag_is_original).attr("data-is_original");
    var update_data = this.getUpdateResource(node_type, node_id);
    var updated_res = $(this.tag_updated_resources).val();
    $.ajaxSetup({beforeSend: function(xhr, settings){xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));}});
    var postdata = {
      "plan_id": plan_id,
      "resource_type": node_type,
      "resource_id": node_id,
      "update_data": JSON.stringify(update_data),
      "updated_res": updated_res,
      "is_original": is_original
    };
    var data = conveyorService.getResourceDetail(postdata);
    if(data) {
      return false;
    }
    $("image#" + node_id).attr("href", data.image);
    var click_img = data.image;
    if(click_img != "") {
      var img_node = $("image[id=image_" + node_id + "]");
      img_node.attr("ori-href", img_node.attr("href"));
      img_node.attr({"href": click_img, "editing": true});
    }
    if(data.data.indexOf("form-group")>-1){
      $("#resource_info_box").html(data.data).css("display", "block");
      $("#conveyor_plan_topology").hide();
      $("#thumbnail").hide();
      $("#stack_box").hide();
    }
    $("select[name='networks'],select[name='routers'],select[name='subnets'],select[name='sgs'],select[name='volumes'],select[name='volumetypes']").parent().parent().css({
        'display':'none'
    });

    $("#id_from_other").parent().click(function(){
        if($("#id_from_other").is(':checked')){
            $("select[name='networks'],select[name='routers'],select[name='subnets'],select[name='sgs'],select[name='volumes'],select[name='volumetypes']").parent().parent().css({
                'display':'block'
            });
        }else{
            $("select[name='networks'],select[name='routers'],select[name='subnets'],select[name='sgs'],select[name='volumes'],select[name='volumetypes']").parent().parent().css({
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
  getUpdateResource: function (resType, resId) {
    var resources = $.parseJSON($(this.tag_update_resource).val());
    for(var index in resources) {
      var res = resources[index];
      if(res.resource_type === resType && res.resource_id === resId) {
        return res;
      }
    }
    return {};
  },
  hideTableInfo: function () {
    $(this.tag_table_info).html("");
    $(this.tag_table_info).css("display", "none");
    $("#conveyor_plan_topology").show();
    $("#thumbnail").show();
    this.clearEditing();
    return false;
  },
  saveTableInfo: function () {
    var self = this;
    try {
      if(self.isUpdating){return false;}
      self.isUpdating = true;
      var need_posted=false;
      var resource_type = $(detailinfo_div).attr("resource_type");
      var resource_id = $(detailinfo_div).attr("resource_id");
      var data = {
        'resource_type': resource_type,
        'resource_id': resource_id
      };
      if(resource_type == "OS::Nova::KeyPair") {
        var kp_node=$("select[name=keypairs]");
        if($(kp_node).attr("data-ori") != $(kp_node).val()){ data["name"] = $(kp_node).val();need_posted=true;}
      } else if(resource_type=="OS::Cinder::Volume") {
        var vols_node=$("select[name=volumes]");
        if($(vols_node).attr("data-ori") != $(vols_node).val()){ data["id"] = $(vols_node).val();need_posted=true;}
        var name_node=$("input#id_name");
        if($(name_node).attr("data-ori") != $(name_node).val()){ data["name"] = $(name_node).val();}
        var desp_node=$("#id_description");
        if($(desp_node).attr("data-ori") != $(desp_node).val()){ data["description"] = $(desp_node).val(); }
        var md_tale=$("table#metadatas");
        if(md_tale.length){
          if(typeof($(md_tale).attr("deleted_ids"))!="undefined" || $(md_tale).find("tr[data_from=client]").length){
            var metadata=[];
            $(md_tale).find("tbody tr:not(.new-row):not(.empty)").each(function(){
              var key = $(this).attr("data-object-id");
              var value = $(this).find("td:last").text();
              metadata.push('"' + $.trim(key) + '":"' + $.trim(value) + '"');
            });
            data["metadata"] = JSON.parse("{"+metadata.join(",")+"}");
          }
        }
      } else if(resource_type === "OS::Neutron::Net") {
        var nets_node=$("select[name=networks]");if($(nets_node).attr("data-ori") != $(nets_node).val()){ data["id"] = $(nets_node).val();need_posted=true;}
        var name_node=$("input#id_name");if($(name_node).attr("data-ori") != $(name_node).val()){ data["name"] = $(name_node).val();}
        var as_node=$("select[name=admin_states]");if($(as_node).attr("data-ori") != $(as_node).val()){ data["admin_state_up"] = $(as_node).val(); }
        var shared_node = $("input#id_shared"); var shared=false; if($(shared_node).is(":checked")){shared=true} if($(shared_node).attr("data-ori")!=shared){data["shared"]=shared}
        var value_specs = {};
        if(self.checkNetworkValueSpecs(value_specs)){data["value_specs"] = value_specs;}
      } else if(resource_type === "OS::Neutron::Port") {
        var changed = false;
        var fixed_ips = [];
        $("input.ip").each(function(){
          var ori_ip = $(this).attr("data-ori"); var ip=$(this).val();
          var alloc = JSON.parse($(this).attr("data-alloc"));
          if(! conveyorUtil.ipCheckInCidr(alloc, ip)) {
            $(this).focus();
            return false;
          }
          if(ori_ip != ip) {
            changed = true;
          }
          fixed_ips.push({"subnet_id": {"get_resource": $(this).attr("data-subnet-id")}, "ip_address": ip});
        });
        if(!changed) {return false;}
        data["fixed_ips"] = fixed_ips;
      } else if(resource_type == "OS::Neutron::Subnet") {
        var subnets_node=$("select[name=subnets]"); if($(subnets_node).attr("data-ori")!=$(subnets_node).val()){data["id"]=$(subnets_node).val(); need_posted=true;}
        var name_node=$("input#id_name"); if($(name_node).attr("data-ori") != $(name_node).val()){ data["name"] = $(name_node).val(); }
        var cidr_node=$("input#id_cidr");
        var cidr=$(cidr_node).val();
        if(!conveyorUtil.checkCidr(cidr, 31)){return false;}
        if($(cidr_node).attr("data-ori") != cidr){ data["cidr"]=cidr }
        var getway_ip_node=$("input#id_gateway_ip"); if($(getway_ip_node).attr("data-ori") != $(getway_ip_node).val()){ data["gateway_ip"] = $(getway_ip_node).val(); }
        if($("input#id_no_gateway").is(":checked")){data["no_gateway"] = true;}else{data["no_gateway"] = false;}
        if($("input#id_enable_dhcp").is(":checked")){data["enable_dhcp"]=true;}else{data["enable_dhcp"]=false}
        var allo_pools_node=$("textarea#id_allocation_pools"); if($(allo_pools_node).attr("data-ori") != $(allo_pools_node).val()){ data["allocation_pools"] = $(allo_pools_node).val(); }
        var dns_node=$("textarea#id_dns_nameservers"); if($(dns_node).attr("data-ori") != $(dns_node).val()){ data["dns_nameservers"] = $(dns_node).val(); }
        var routes_node=$("textarea#id_host_routes");if($(routes_node).attr("data-ori") != $(routes_node).val()){ data["host_routes"] = $(routes_node).val(); }
      } else if(resource_type == "OS::Neutron::SecurityGroup") {
        var sgs_node=$("select[name=sgs]");
        if(sgs_node.length){if($(sgs_node).attr("data-ori")!=$(sgs_node).val()){data["id"]=$(sgs_node).val(); need_posted=true;}}
        var sgr_node = $("#id_sgrs");
        if(sgr_node.length){
          var rules = $(sgr_node).attr("data-ori");
          var t_rules = $("div#resource_info_box table#rules");
          if($(t_rules).length){
            if(typeof($(t_rules).attr("deleted_ids"))!="undefined"){
              var json_rs = $.parseJSON(rules);
              var deleted_r_ids = $(t_rules).attr("deleted_ids").split(' ');
              for(index in deleted_r_ids){
                var id = deleted_r_ids[index];
                for(var r in json_rs){
                  if(json_rs[r]['id'] == id){json_rs.splice(r, 1);break;}
                }
              }
              data["rules"] = JSON.stringify(json_rs);
            }else if($(sgr_node).attr('changed') == "true"){
              data["rules"] = rules
            }
          }else if($(sgr_node).attr('changed') == "true"){
            data["rules"] = rules
          }
        }
      } else {
        var has_matched_id = false;
        for(key in res_items) {
          if(key==resource_type) {
            has_matched_id = true;
            break;
          }
        }
        if(!has_matched_id) {
          return false;
        }

        //var need_posted = false;
        for(var key in res_items[resource_type]) {
          var value = res_items[resource_type];
          var index, node_name, slt_items, slt_node, metaNode;
          if(key === ipt){
            var ipt_items = value[ipt];
            for(index in ipt_items){
              node_name = ipt_items[index];
              self.getInputData(node_name, data);
            }
          }else if(key === slt){
            slt_items = value[slt];
            for(index in slt_items){
              node_name = slt_items[index];
              self.getSelectData(node_name, data);
            }
          }else if(key === slt_from_existed){
            slt_items = value[slt_from_existed];
            for(index in slt_items){
              node_name = slt_items[index];
              if(self.getDataFromExisted(node_name, data)) {
                need_posted=true;
              }
            }
          } else if(key === meta) {
            metaNode = value[meta];
            var nodeName = 'div#resource_info_box table#metadatas';
            self.getMetaTableData(nodeName, data);
          }
        }
      }
      var len=0;
      $.each(data, function (k, v) {
        len++
      });
      if(len!=2){if(need_posted){
        self.resChanged(resource_type, resource_id, data);
      }else{
        self.updateResourceName(resource_id, data);
        self.saveChangedInfo(resource_type, resource_id, data);
      }
      }
      $(self.tag_table_info).html("");
      $(self.tag_table_info).css("display", "none");
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
  /*
   * Check input field(textbox, select) data is changed, if yes, update it to dstDict
   */
  getInputData: function (nodeName, dstDict) {
    var selector = '#id_' + nodeName;
    var inputEle = $(selector);
    if($(inputEle).attr("data-ori") != $(inputEle).val()) {
      dstDict[nodeName] = $(inputEle).val();
      return true;
    }
    return false;
  },
  /*
   * Check input field(checkbox) data is changed, if yes, update it to dstDict
   */
  getChkData: function (nodeName, dstDict) {
    var selector = '#id_' + nodeName;
    var chkEle = $(selector);
    var checked = $(chkEle).is(":checked");
    if($(chkEle).attr("data-ori") != checked) {
      dstDict[nodeName] = checked;
      return true;
    }
    return false;
  },
  getSelectData: function (nodeName, dstDict) {
    var selector = "select[name=" + nodeName + "s]";
    var inputEle = $(selector);
    if($(inputEle).attr("data-ori") != $(inputEle).val()) {
      dstDict[nodeName] = $(inputEle).val();
      return true;
    }
    return false;
  },
  /* Change resource from ori to other res
   * params
   * nodeName: generally, it is the sort resource type, link volume, net
   * dstDict:  */
  getDataFromExisted: function (nodeName, dstDict) {
    var selector = '[name=' + nodeName + ']';
    var slt_node = $(selector);
    if($(slt_node).val() != $(slt_node).attr("data-ori")) {
      dstDict["id"] = $(slt_node).val();
      return true;
    }
    return false;
  },
  getMetaTableData: function (nodeName, dstDict) {
    var metaTable = $('div#resource_info_box table#metadatas');
    if(metaTable.length == 0) {
      return false;
    }

    if(typeof $(metaTable).attr('deleted_ids') != 'undefined' || $(metaTable).find('tr[data_from=client]').length) {
      var metadata = [];
      $(metaTable).find("tbody tr:not(.new-row):not(.empty)").each(function () {
        var key = $(this).attr("data-object-id");
        var value = $(this).find("td:last").text();
        metadata.push('"' + $.trim(key) + '":"' + $.trim(value) + '"');
      });
      dstDict['metadata'] = $.parseJSON("{"+metadata.join(",")+"}");
      return true;
    }
    return false;
  },
  checkNetworkValueSpecs: function (valueSpecs) {
    var modified = false;
    var seg_node = $("#id_segmentation_id");
    if(seg_node.length == 1) {
      valueSpecs["segmentation_id"] = $(seg_node).val();
      if($(seg_node).attr("data-ori") != $(seg_node).val()) {
        modified = true;
      }
    }
    var phy_net_node = $("#id_physical_network");
    if(phy_net_node.length == 1) {
      valueSpecs["physical_network"] = $(phy_net_node).val();
      if($(phy_net_node).attr("data-ori") != $(phy_net_node).val()) {
        modified = true;
      }
    }
    var net_type_node = $("#id_network_type");
    if(net_type_node.length==1) {
      valueSpecs["network_type"] = $(net_type_node).val();
      if($(net_type_node).attr("data-ori") != $(net_type_node).val()) {
        modified = true;
      }
    }
    var router_external_node = $("#id_router_external");
    if(router_external_node.length==1) {
      valueSpecs["router_external"] = $(router_external_node).val()
    }
    return modified;
  },
  /* In dashboard, change resource's some propertity, them submit it to backend to resolve.
   * params:
   * resType:	resource type in plan. like OS::Nova::Server.
   * resId:		resource id in plan. like server_0.
   * data:		data changed to resource.
   * */
  resChanged: function (resType, resId, data) {
    var self = this;
    var plan_id = $(self.tag_plan_id).val();
    var updated_resources = $(self.tag_updated_resources).val();
    var dependencies = $(self.tag_dependencies).val();
    var update_resource = $(self.tag_update_resource).val();
    $.ajaxSetup({beforeSend: function(xhr, settings){xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));}});
    var postdata = {
      "plan_id": plan_id,
      "resource_type": resType,
      "resource_id": resId,
      "updated_resources": updated_resources,
      "dependencies": dependencies,
      "update_res": update_resource,
      "data": JSON.stringify(data)
    };
    $.post(get_update_plan_url(plan_id), postdata,function(json){
      update_topo(JSON.parse(json.d3_data));
      this.updatePlanDeps(json.res_deps);
      for(var index in json.update_resources) {
        var item = json.update_resources[index];
        self.saveChangedInfo(item.resource_type,item.resource_id, item);
      }
      $(self.tag_updated_resources).val(JSON.stringify(json.updated_resources));
      $(self.tag_dependencies).val(JSON.stringify(json.dependencies));
     });
  },
  saveChangedInfo: function (resType, resId, data) {
    var self = this;
    var data_from = $(self.tag_update_resource).val();
    data_from = $.parseJSON(data_from);
    for(var index in data_from) {
      var update_res = data_from[index];
      if(update_res.resource_type === resType && update_res.resource_id === resId) {
        conveyorUtil.merge(update_res, data);
        $(self.tag_update_resource).val(JSON.stringify(data_from));
        return;
      }
    }
    data_from.push(data);
    $(self.tag_update_resource).val(JSON.stringify(data_from));
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
    self.configLocalTopology();
  },
  configLocalTopology: function (){
    var self = this;
    var plan_deps_table = $('#plan_deps_table');
    $(plan_deps_table).find('tbody tr').each(function () {
      $(this).find('td:last a').click(function () {
        if($(self.tag_table_info).length) {
          $(self.tag_table_info).hide();
        }
        showTopology();
        try{
          redraw($(this).attr('href'));
          return false
        } catch(e) {
          return false;
        }
      });
    });
    $("#plan_deps").treeTable();
  },
  updateResourceName: function (resId, data) {
    $.each(data, function (k, v) {
      if(k=='name'){
        $("#plan_deps").find('#plan_deps__row__'+res_id).find('td:eq(1)').text(v);
        $("#conveyor_plan_topology .node").each(function(){
          if($(this).attr("node_id") == resId){
            var node_info = $(this).context.__data__.info_box;
            var new_info = node_info.replace(/<h3>.*<\/h3>/g,"<h3>Name:"+v+"</h3>");
            $(this).on("mouseover", function(){
              $("#info_box").html(new_info);
            });
            $(this).on("mouseout",function(){
              $("#info_box").html("");
            });
          }
        });
      }
    });
  },
  /* For resource detail. Allow to add some items for property with type of list
   * of detail resource.
   * params:
   * t_seletor: 			js selector of the table being to operate.
   * t_type: 				the type (or name) of table. like: metadatas, rules
   * add_action_selector: js selector of the add action button.*/
  openAddOperation: function (t_selector, t_type, add_action_selector) {
    var self = this;
    if($(add_action_selector).length){
      $(add_action_selector).click(function(){
        if(t_type == "metadatas"){
          if(!$(t_selector).find("tr.new-row").length){
            $(t_selector).find("tbody").prepend('<tr class="new-row"><td class="multi_select_column"><td class="sortable normal_column"><input name="key" class="form-control" onkeydown="if(event.keyCode==13){conveyorEditPlanRes.addMetaForServer(\'table#metadatas\')}"/></td><td class="sortable normal_column"><input name="value" class="form-control" onkeydown="if(event.keyCode==13){conveyorEditPlanRes.addMetaForServer(\'table#metadatas\')}"/></td></tr>')
          }
        }else if(t_type == "rules"){
          if($("#resource_info_box form#create_security_group_rule_form").length){return;}
          $.get(rootPath+"/conveyor/plans/"+$('#secgroup_wrap').attr('os_id')+"/add_rule/", function(rsp){
            var form = $(rsp).find("form#create_security_group_rule_form");
            $(form).append($(form).find("div.col-sm-6:first").html()).find("div.modal-body").remove();
            $(form).find("div.modal-footer").remove();
            $(form).append("<div class=\"footer\"><div class=\"cell delete\"><div class=\"cancel btn btn-danger btn-xs\">Cancel</div><div id=\"id_add_sg_rule\" onclick='conveyorEditPlanRes.addSGRuleForSG()' class=\"add-rule btn btn-danger btn-xs\">Add</div></div></div>");
            $("#resource_info_box div.footer").after($(form).prop("outerHTML"));
            $("#id_rule_menu").trigger('change', $("#id_rule_menu").children().eq(1));
          });
          return false;
        }
      });
    }
  },
  /* For resource detail. All to delete some items for property with type of list
   * of detail resource.
   * params:
   * t_seletor:			js selector of the table being to operate.
   * del_action_selector: js selector of the delete action button.*/
  openDeleteOperation: function (t_seletor, del_action_selector) {
    if($(del_action_selector).length){$(del_action_selector).click(function(){rm_table_items(t_seletor, del_action_selector);return false;});}
    $(t_seletor).find("thead input.table-row-multi-select").click(function(){
      if ($(this).attr("checked") == "checked") {
        if($(del_action_selector).hasClass("disabled")){$(del_action_selector).removeClass("disabled");}
      } else {
        if(!$(del_action_selector).hasClass("disabled")){$(del_action_selector).addClass("disabled");}
      }
    });
    $(t_seletor).find("tbody input.table-row-multi-select").click(function(){
      if($(t_seletor).find("tbody input.table-row-multi-select").length){
        if($(del_action_selector).hasClass("disabled")){
          $(del_action_selector).removeClass("disabled");
        }
      }else{
        if(!$(del_action_selector).hasClass("disabled")){
          $(del_action_selector).addClass("disabled");
        }
      }
    });
  },
  /* Remove items for table temporary. while not delete behind
   * params:
   * selector:			the css selector of the table being to operate.
   * del_action_selector: js selector of the delete action button.*/
  removeTableItems: function (t_selector, del_action_selector) {
    $(t_selector).find("tbody tr").each(function(){
      if($(this).find("input[name=object_ids].table-row-multi-select").attr("checked")=="checked"){
        var item_id = $(this).attr("data-object-id");
        if(typeof($(t_selector).attr("deleted_ids"))=="undefined"){$(t_selector).attr("deleted_ids", item_id);}
        else{$(t_selector).attr("deleted_ids", $(t_selector).attr("deleted_ids") + " " + item_id);}
        $(this).remove();
      }
    });
    if(!$(del_action_selector).hasClass("disabled")){$(del_action_selector).addClass("disabled");}
  },
  /* For resource detail. Add an new metadata item for instance metadata property.
   * params:
   * selector: js selector of metadata table.*/
  addMetaForServer: function (selector) {
    var in_key = $(selector).find("tbody tr.new-row input[name=key]");
    var in_value = $(selector).find("input[name=value]");
    var key = $(in_key).val();
    var value = $(in_value).val();
    if(key==""){$(in_key).focus();return;}
    if(value==""){$(in_value).focus();return;}
    var row = '<tr data_from="client" data-object-id="' + key + '" id="metadatas__row__' + key + '">'
          + '<td class="multi_select_column"><input class="table-row-multi-select" name="object_ids" type="checkbox" value="' + key + '"></td>'
          + '<td class="sortable normal_column">' + key + '</td>'
          + '<td class="sortable normal_column">' + value + '</td></tr>';
    $(selector).find("tr.new-row").remove();
    $(selector).find("tbody").prepend(row);
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

    var result = conveyorService.createSGRule($("#secgroup_wrap").attr('od_id'), {'secgroup_rule': JSON.stringify(secgroup_rule)});
    if(result) {
       var sgr = result.sgr;
        var sgrs_node = $("#id_sgrs");
        var ori_rs = $.parseJSON($(sgrs_node).attr("data-ori"));
        ori_rs.push(sgr);
        $(sgrs_node).attr({"data-ori": JSON.stringify(ori_rs), "changed": true});
        $("table#rules tbody").append($(result.sgr_html).find("tbody tr").prop("outerHTML"));
        $("form#create_security_group_rule_form").remove();
        return false;
    }
  }
};
