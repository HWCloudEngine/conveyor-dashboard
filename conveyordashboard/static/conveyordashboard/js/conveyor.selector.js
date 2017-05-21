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

    var clone_plan_topology = "a.create-clone-plan-for-mul-sel";
    var migrate_plan_topology = "a.create-migrate-plan-for-mul-sel";
    var multi_sel_action = [clone_plan_topology, migrate_plan_topology];
    var multi_sel_action_map = {
        "clone": clone_plan_topology,
        "migrate": migrate_plan_topology
    };
    var clone_ids = {};
    var migrate_ids = {};
    var plan_type_ids_map = {
        "clone": clone_ids,
        "migrate": migrate_ids
    };

    function get_table_res_type(table){
        var classes = $(table).attr("class").split(" ");
        for(var index=0;index<classes.length;index++){
        var css_class = classes[index];
            if(css_class.startsWith("OS::")){
                return css_class;
            }
        }
        return "";
    }
    function check_topology_link() {
        $.each(multi_sel_action_map, function (plan_type, selector) {
            if($(selector).length === 0) {return;}
            var len = 0;
            $.each(plan_type_ids_map[plan_type], function (k, v) {
                len += v.length;
            });
            if(len > 0){
                if($(selector).hasClass("disabled")){$(selector).removeClass("disabled");}
            }else{
                if(!$(selector).hasClass("disabled")){$(selector).addClass("disabled");}
            }
        })
    }
    function get_query_string(plan_type){
        var id_strs=[];
        $.each(plan_type_ids_map[plan_type], function (k, v) {
            if (v.length > 0) {
                id_strs.push(k+"*"+v.join(","));
            }
        });
        return "?ids="+id_strs.join("**");
    }

    var $create_clone_plan_topology = function(){
        var href = $(this).attr("href").split("?")[0];
        href+=get_query_string("clone");
        $(this).attr("href", href);
        return true;
    };
    var $create_migrate_plan_topology = function(){
        var href = $(this).attr("href").split("?")[0];
        href+=get_query_string("migrate");
        $(this).attr("href", href);
        return true;
    };
    $(function(){
        if($(multi_sel_action).length){
            if($(clone_plan_topology).length){$(clone_plan_topology).click($create_clone_plan_topology);}
            if($(migrate_plan_topology).length){$(migrate_plan_topology).click($create_migrate_plan_topology);}

            $("table.table-res").each(function(){
                var type = get_table_res_type(this);
                var this_table = this;
                $(this).find("thead input.table-row-multi-select").click(function(){
                    if ($(this).attr("checked") == "checked") {
                        var tmp_clone_ids = [];
                        var tmp_migrate_ids = [];
                        $(this_table).find("tbody tr").each(function(){
                            $(this).find("td.actions_column .btn-clone").length > 0 && tmp_clone_ids.push($(this).find("input[type=checkbox][name=object_ids]")[0].value);
                            $(this).find("td.actions_column .btn-migrate").length > 0 && tmp_migrate_ids.push($(this).find("input[type=checkbox][name=object_ids]")[0].value);
                        });
                        clone_ids[type] = tmp_clone_ids;
                        migrate_ids[type] = tmp_migrate_ids;
                    } else {
                        clone_ids[type] = migrate_ids[type] = [];
                    }
                    check_topology_link();
                });
                $(this).find("tbody tr").each(function () {
                    var tr = this;
                    $(this).find("input.table-row-multi-select").click(function () {
                        var uuid = $(this).val();
                        var tmp_clone_ids = [];
                        var tmp_migrate_ids = [];
                        if(plan_type_ids_map["clone"].hasOwnProperty(type)) {tmp_clone_ids = clone_ids[type];}
                        if(plan_type_ids_map["migrate"].hasOwnProperty(type)) {tmp_migrate_ids = migrate_ids[type];}
                        if($(this).attr("checked") == "checked") {
                            if($.inArray(uuid, tmp_clone_ids) === -1) {
                                if($(tr).find("td.actions_column .btn-clone").length) {tmp_clone_ids.push(uuid)}
                            }
                            if($.inArray(uuid, tmp_migrate_ids) === -1) {
                                if($(tr).find("td.actions_column .btn-migrate").length) {tmp_migrate_ids.push(uuid)}
                            }
                        } else {
                            var index = $.inArray(uuid, tmp_clone_ids);
                            if(index !== -1) {
                                tmp_clone_ids.splice(index, 1)
                            }
                            index = $.inArray(uuid, tmp_migrate_ids);
                            if(index !== -1) {
                                tmp_migrate_ids.splice(index, 1)
                            }
                        }
                        clone_ids[type] = tmp_clone_ids;
                        migrate_ids[type] = tmp_migrate_ids;
                        check_topology_link();
                    });
                });
            });
        }
    });
});