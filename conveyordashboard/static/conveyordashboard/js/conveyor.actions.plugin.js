var conveyor_action_url = "/conveyor/overview/row_actions";
var conveyor_table_action_url = "/conveyor/overview/table_actions";
var next_url = window.location.href;

var inst_table_id = "table#instances";
var vol_table_id = "table#volumes";
var net_table_id = "table#networks";
var secg_table_id = "table#security_groups";
var fip_table_id = "table#floating_ips";
var pools_table_id = "table#poolstable";
var allowed_res_table_ids = [inst_table_id, vol_table_id, net_table_id, secg_table_id, fip_table_id, pools_table_id];

var table_res_type_mappings = {
	"instances":"OS::Nova::Server",
	"volumes":"OS::Cinder::Volume",
	"networks":"OS::Neutron::Net",
	"security_groups":"OS::Neutron::SecurityGroup",
	"floating_ips":"OS::Neutron::FloatingIP",
	"poolstable":"OS::Neutron::Pool"
};

var conveyor_clone_plan_topology = "a.create-clone-plan-for-mul-sel";
var conveyor_migrate_plan_topology = "a.create-migrate-plan-for-mul-sel";
var conveyor_multi_sel_action = [conveyor_clone_plan_topology, conveyor_migrate_plan_topology];
var conveyor_ids = {};

function conveyor_get_query_string(){
	url="?next_url=" + next_url +"&ids=";
	id_strs=[];
	for(key in conveyor_ids){
		if (conveyor_ids[key].length > 0) {
			id_strs.push(key+"*"+conveyor_ids[key].join(","));
		}
	}
	url+=id_strs.join("**");
	return url;
}

function conveyor_clone_get_url(){
	return "/conveyor/plans/clone";
}

function conveyor_migrate_get_url(){
	return "/conveyor/plans/migrate";
}

var $conveyor_create_plan_topology = function(){
	href = conveyor_clone_get_url();
	if(href == "") { href = $(this).attr("href")}
	href += conveyor_get_query_string() + "&type=clone";
	$(this).attr("href", href);
	return true;
};

var $conveyor_create_migrate_plan_topology = function(){
	href = conveyor_migrate_get_url();
	if(href == "") { href = $(this).attr("href")}
	href += conveyor_get_query_string() + "&type=migrate";
	$(this).attr("href", href);
	return true;
};

function conveyor_check_topology_link(){
	len = 0;
	for(index in conveyor_ids){
		len += conveyor_ids[index].length;
	}
	for(index in conveyor_multi_sel_action) {
		action = conveyor_multi_sel_action[index];
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
		actions = $(rsp);
		action_ids = ["a#type__row_id__action_clone_plan", "a#type__row_id__action_migrate_plan"]
		for(index in action_ids){
			var action_id = action_ids[index];
			action_id = action_id.replace(/type/g, table_type);
			action_id = action_id.replace(/id/g, res_id);
			
			if($(actions).find(action_id).length == 0) {continue;}
			action = $(actions).find(action_id);
			$(tr).find("td.actions_column ul").append("<li class=\"clearfix\">"+$(action).prop("outerHTML")+"</li>");
		}
	});
}

function get_table_action(data, table, table_type){
	$.get(conveyor_table_action_url, data, function(rsp){
		actions = $(rsp);
		action_ids = ["a#type__action_create_plan_with_mul_res", "a#type__action_create_migrate_plan_with_mul_res"]
		for(index in action_ids){
			var action_id = action_ids[index];
			action_id = action_id.replace(/type/g, table_type);
			
			action = $(actions).find(action_id);
			if($(actions).find(action_id).length == 0) {continue;}
			
			if($(table).find("thead tr.table_caption div.table_actions div.table_actions_menu").length){
				$(table).find("thead tr.table_caption div.table_actions div.table_actions_menu").before($(action).prop("outerHTML"));
			}else {
				$(table).find("thead tr.table_caption div.table_actions").append($(action).prop("outerHTML"));
			}
		}
		
		if($(conveyor_clone_plan_topology).length){$(conveyor_clone_plan_topology).click($conveyor_create_plan_topology);}
		if($(conveyor_migrate_plan_topology).length){$(conveyor_migrate_plan_topology).click($conveyor_create_migrate_plan_topology);}
		
		var type = table_res_type_mappings[$(table).attr("id")];
		$(table).find("thead input.table-row-multi-select").click(function(){
			if ($(this).attr("checked") == "checked") {
				tmp_ids = [];
				$(table).find("input[type=checkbox][name=object_ids]").each(function(){tmp_ids.push($(this).val());});
				conveyor_ids[type] = tmp_ids;
			} else {
				conveyor_ids[type]=[];
			}
			conveyor_check_topology_link();
		});
		$(table).find("tbody input.table-row-multi-select").click(function(){
			id = $(this).val();
			tmp_ids = [];
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

$(function(){
	for(index in allowed_res_table_ids){
		table_id = allowed_res_table_ids[index];
		if($(table_id).length){
			res_table = $(table_id);
			table_type = $(res_table).attr("id");
			res_type = table_res_type_mappings[table_type];
			
			if($(res_table).attr("class").indexOf("OS::") >= 0){return;}
			
			//contains empty row means that does not contains data rows.
			if($(res_table).find("tbody tr.empty").length){return;}
			
			//table_actions
			if($(res_table).find("tbody tr").length){get_table_action({"res_type": res_type, "next_url": next_url}, res_table, table_type);}
			
			//row_actions
			$(res_table).find("tbody tr").each(function(){
				tr = this;
				id = $(this).find("td.multi_select_column input.table-row-multi-select").val();
				data = {"id": id, "res_type": res_type, "next_url": next_url};
				get_row_action(data, table_type, tr, id);
			});
		}
	}
});