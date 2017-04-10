var clone_plan_topology = "a.create-clone-plan-for-mul-sel";
var migrate_plan_topology = "a.create-migrate-plan-for-mul-sel";
var multi_sel_action = [clone_plan_topology, migrate_plan_topology];
var ids = {};

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
function check_topology_link(){
    var len = 0;
    $.each(ids, function (k, v) {
        len += v.length;
    });
    for(var index=0;index<multi_sel_action.length;index++) {
        var action = multi_sel_action[index];
        if($(action).length == 0) {return;}
        if(len > 0){
            if($(action).hasClass("disabled")){$(action).removeClass("disabled");}
        }else{
            if(!$(action).hasClass("disabled")){$(action).addClass("disabled");}
        }
    }
}
function get_query_string(){
    var id_strs=[];
    $.each(ids, function (k, v) {
        if (v.length > 0) {
            id_strs.push(k+"*"+v.join(","));
        }
    });
    return '?ids='+id_strs.join("**");
}

var $create_clone_plan_topology = function(){
    var href = $(this).attr('href').split('?')[0];
    href+=get_query_string();
    $(this).attr('href', href);
    return true;
};
var $create_migrate_plan_topology = function(){
    var href = $(this).attr('href').split('?')[0];
    href+=get_query_string();
    $(this).attr('href', href);
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
                    var tmp_ids = [];
                    $(this_table).find("tbody tr").each(function(){
                        // TODO(drngsl) here, use clone action mark clone and migrate.
                        $(this).find("td.actions_column .btn-clone").length > 0 && tmp_ids.push($(this).find("input[type=checkbox][name=object_ids]")[0].value);
                    });
                    ids[type] = tmp_ids;
                } else {
                    ids[type]=[];
                }
                check_topology_link();
            });
            $(this).find("tbody tr").each(function () {
                var tr = this;
                $(this).find("input.table-row-multi-select").click(function () {
                    // TODO(drngsl) here, use clone action mark clone and migrate.
                    if($(tr).find("td.actions_column .btn-clone").length == 0){return;}
                    var uuid = $(this).val();
					var tmp_ids = [];
                    if(ids.hasOwnProperty(type)) {tmp_ids = ids[type];}
                    if($(this).attr("checked") == "checked") {
                        if($.inArray(uuid, tmp_ids) === -1) {
                            tmp_ids.push(uuid)
                        }
					} else {
                        var index = $.inArray(uuid, tmp_ids);
                        if(index !== -1) {
                            tmp_ids.splice(index, 1)
                        }
                    }
                    ids[type] = tmp_ids;
					check_topology_link();
				});
            });
        });
    }
});