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
  var rootPath = WEBROOT;
  var conveyor_action_url = rootPath + "/conveyor/overview/row_actions";
  var conveyor_table_action_url = rootPath + "/conveyor/overview/table_actions";
  var conveyor_clone_url = rootPath + "/conveyor/plans/clone";
  var conveyor_migrate_url = rootPath + "/conveyor/plans/migrate";
  var next_url = window.location.href;

  var inst_table_id = "table#instances";
  var vol_table_id = "table#volumes";
  var net_table_id = "table#networks";
  var secg_table_id = "table#security_groups";
  var fip_table_id = "table#floating_ips";
  var pools_table_id = "table#poolstable";
  var allowed_res_table_ids = [inst_table_id, vol_table_id, net_table_id, secg_table_id, fip_table_id, pools_table_id];

  var table_res_type_mappings = {
    "instances": "OS::Nova::Server",
    "volumes": "OS::Cinder::Volume",
    "networks": "OS::Neutron::Net",
    "security_groups": "OS::Neutron::SecurityGroup",
    "floating_ips": "OS::Neutron::FloatingIP",
    "poolstable": "OS::Neutron::Pool"
  };

  var table_actions_cls = "caption div.table_actions";
  var table_actions_menu_cls = "div.table_actions_menu";
  var actions_column_cls = "td.actions_column";
  var conveyor_clone_plan_topology = "a.create-clone-plan-for-mul-sel";
  var conveyor_migrate_plan_topology = "a.create-migrate-plan-for-mul-sel";
  var conveyor_multi_sel_action = [conveyor_clone_plan_topology, conveyor_migrate_plan_topology];
  var conveyor_ids = {};

  function conveyor_get_query_string(){
    var url = "?next_url=" + next_url + "&ids=";
    var id_strs = [];
    for(var key in conveyor_ids){
      if (conveyor_ids[key].length > 0) {
        id_strs.push(key + "*" + conveyor_ids[key].join(","));
      }
    }
    url += id_strs.join("**");
    return url;
  }

  var $conveyor_create_plan_topology = function(){
    var href = conveyor_clone_url + conveyor_get_query_string() + "&type=clone";
    $(this).attr("href", href);
    return true;
  };

  var $conveyor_create_migrate_plan_topology = function(){
    var href = conveyor_migrate_url + conveyor_get_query_string() + "&type=migrate";
    $(this).attr("href", href);
    return true;
  };

  function conveyor_check_topology_link(){
    var len = 0;
    for(var index in conveyor_ids){
      len += conveyor_ids[index].length;
    }
    for(index in conveyor_multi_sel_action) {
      var action = conveyor_multi_sel_action[index];
      if($(action).length == 0) {return;}
      if(len > 0){
        if($(action).hasClass("disabled")){$(action).removeClass("disabled");}
      }else{
        if(!$(action).hasClass("disabled")){$(action).addClass("disabled");}
      }
    }
  }

  function get_row_action(data, table_type, tr, res_id){
    $.get(conveyor_action_url, data, function(rsp){
      var actions = $.parseHTML(rsp);
      var action_ids = ["a#type__row_id__action_clone_plan", "a#type__row_id__action_migrate_plan"];
      for(var index in action_ids){
        var action_id = action_ids[index];
        action_id = action_id.replace(/type/g, table_type).replace(/id/g, res_id);

        if($(actions).find(action_id).length == 0) {continue;}
        var action = $(actions).find(action_id);
        var actions_column = $(tr).find(actions_column_cls);
        if($(actions_column).children().length > 0) {
          action.removeClass("btn");
          var ul = $(actions_column).find("ul");
          if(ul.length > 0) {
            $(ul).append("<li>" + $(action).prop("outerHTML") + "</li>");
          } else {
            $(actions_column).children().addClass("btn-sm");
            $(actions_column).width($(actions_column).width() + 30);
            $(actions_column).append('<a class="btn btn-default btn-sm dropdown-toggle" data-toggle="dropdown" href="#"><span class="fa fa-caret-down"></span></a>');
            $(actions_column).append("<ul class=\"dropdown-menu dropdown-menu-right row_actions\"><li>" + $(action).prop("outerHTML") + "</li></ul>");
          }
        }
        else {
          $(actions_column).append($(action))
        }
      }
    });
  }

  function get_table_action(data, table, table_type){
    $.get(conveyor_table_action_url, data, function(rsp){
      var actions = $.parseHTML(rsp);
      var action_ids = ["a#type__action_create_plan_with_mul_res", "a#type__action_create_migrate_plan_with_mul_res"];
      for(var index in action_ids){
        var action_id = action_ids[index].replace(/type/g, table_type);

        if($(actions).find(action_id).length == 0) {continue;}
        var action = $(actions).find(action_id);

        var table_actions = $(table).find(table_actions_cls);
        if(table_actions) {
          if($(table_actions).find(table_actions_menu_cls)) {
            $(table_actions).children(table_actions_menu_cls).before($(action).prop("outerHTML"));
          }
          else{
            $(table_actions).append($(action).prop("outerHTML"))
          }
        }
      }

      if($(conveyor_clone_plan_topology).length){$(conveyor_clone_plan_topology).click($conveyor_create_plan_topology);}
      if($(conveyor_migrate_plan_topology).length){$(conveyor_migrate_plan_topology).click($conveyor_create_migrate_plan_topology);}

      var type = table_res_type_mappings[$(table).attr("id")];
      $(table).find("thead input.table-row-multi-select").click(function(){
        if ($(this).attr("checked") == "checked") {
          var tmp_ids = [];
          $(table).find("input[type=checkbox][name=object_ids]").each(function(){tmp_ids.push($(this).val());});
          conveyor_ids[type] = tmp_ids;
        } else {
          conveyor_ids[type]=[];
        }
        conveyor_check_topology_link();
      });
      $(table).find("tbody input.table-row-multi-select").click(function(){
        var id = $(this).val();
        var tmp_ids = [];
        if(conveyor_ids.hasOwnProperty(type)) {tmp_ids = conveyor_ids[type];}
        if($(this).attr("checked") == "checked") {
          if($.inArray(id, tmp_ids) == -1) {
            tmp_ids.push(id);
          }
        } else {
          index = $.inArray(id, tmp_ids);
          if(index != -1) {
            tmp_ids.splice(index, 1);
          }
        }
        conveyor_ids[type]=tmp_ids;
        conveyor_check_topology_link();
      });
    });
  }

  for(var index in allowed_res_table_ids){
    var table_id = allowed_res_table_ids[index];
    if($(table_id).length){
      var res_table = $(table_id);
      var table_type = $(res_table).attr("id");
      var res_type = table_res_type_mappings[table_type];

      if($(res_table).attr("class").indexOf("OS::") >= 0){return;}

      //contains empty row means that does not contains data rows.
      if($(res_table).find("tbody tr.empty").length){return;}

			//table_actions
      if($(res_table).find("tbody tr").length){get_table_action({"res_type": res_type, "next_url": next_url}, res_table, table_type);}

      //row_actions
      $(res_table).find("tbody tr").each(function(){
        var tr = this;
        var id = $(this).find("td.multi_select_column input.table-row-multi-select").val();
        var data = {"id": id, "res_type": res_type, "next_url": next_url};
        get_row_action(data, table_type, tr, id);
      });
    }
  }
});
