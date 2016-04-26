var checkbox_for_all = "div.tablesorter-header-inner input[type=checkbox].table-row-multi-select"
var checkbox_for_instance = "input[type=checkbox][name=object_ids].table-row-multi-select";
var clone_plans = "a#instances__action_clone_plan";
var plan_topology = "a.create-plan-for-mul-sel";
var migrate_plan_topology = "a.create-migrate-plan-for-mul-sel";
var multi_sel_action = [plan_topology, migrate_plan_topology];
var inst_ids = [];
var insts = null;
var ids = {}

var $checkbox_for_instance_click = function() {
	inst_id = $(this).val();
	if ($(this).attr("checked") == "checked") {
		if($.inArray(inst_id, inst_ids) === -1) {
			inst_ids.push(inst_id);			
		}
	} else {
		var index = $.inArray(inst_id, inst_ids);
		if(index != -1) {
			inst_ids.splice(index, 1);
		}
	}
	$(clone_plans).attr('href', '/conveyor/' + inst_ids.join(",") + '/clone_plan')
}

var $checkbox_for_all = function() {
	inst_id = $(this).val();
	if ($(this).attr("checked") == "checked") {
		if($.inArray(inst_id, inst_ids) === -1) {
			inst_ids.push(inst_id);			
		}
	} else {
		var index = $.inArray(inst_id, inst_ids);
		if(index != -1) {
			inst_ids.splice(index, 1);
		}
	}
	$(clone_plans).attr('href', '/conveyor/' + inst_ids.join(",") + '/clone_plan')
}

$(function(){
	insts = $(checkbox_for_instance)
	insts.bind('change',$checkbox_for_instance_click);
	$(clone_plans).click(function(){
		if(insts === null)
			return false;
		insts.each($checkbox_for_instance_click);
		if(inst_ids.length > 0) {
			return true
		}
		return false;
	})
})

function get_table_res_type(table){classes = $(table).attr("class").split(" ");for(index in classes){css_class = classes[index];if(css_class.startsWith("OS::")){return css_class;}}return "";}
function check_topology_link(){
	len = 0;
	for(index in ids){
		len += ids[index].length;
	}
	for(index in multi_sel_action) {
		action = multi_sel_action[index];
		if($(action).length == 0) {return;}
		if(len > 0){
			if($(action).hasClass("disabled")){$(action).removeClass("disabled");}
		}else{
			if(!$(action).hasClass("disabled")){$(action).addClass("disabled");}
		}
	}
}
function get_query_string(){
	url="?next_url="+window.location.href+"&ids=";
	id_strs=[];
	for(key in ids){
		if (ids[key].length > 0) {
			id_strs.push(key+"*"+ids[key].join(","));
		}
	}
	url+=id_strs.join("**");
	return url;
}
function get_url(){return "/conveyor/overview/create_plan";}
var $create_plan_topology = function(){
	href = get_url();
	if(href == "") { href = $(this).attr("href")}
	href += get_query_string() + "&type=clone";
	$(this).attr("href", href);
	return true;
}
var $create_migrate_plan_topology = function(){
	href = get_url();
	if(href == "") { href = $(this).attr("href")}
	href += get_query_string() + "&type=migrate";
	$(this).attr("href", href);
	return true;
}
$(function(){
	if($(multi_sel_action).length){
		if($(plan_topology).length){$(plan_topology).click($create_plan_topology);}
		if($(migrate_plan_topology).length){$(migrate_plan_topology).click($create_migrate_plan_topology);}
		
		$("table.table-res").each(function(){
			var type = get_table_res_type(this);
			var this_table = this;
			$(this).find("thead input.table-row-multi-select").click(function(){
				if ($(this).attr("checked") == "checked") {
					tmp_ids = [];
					$(this_table).find("input[type=checkbox][name=object_ids]").each(function(){tmp_ids.push($(this).val());});
					ids[type] = tmp_ids;
				} else {
					ids[type]=[];
				}
				check_topology_link();
			});
			$(this).find("tbody input.table-row-multi-select").click(function(){
				id = $(this).val();
				tmp_ids = [];
				if(ids.hasOwnProperty(type)) {tmp_ids = ids[type];}
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
				ids[type]=tmp_ids;
				check_topology_link();
			});
		});
	}
})