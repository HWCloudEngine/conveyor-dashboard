////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
var RESOURCE_TYPE = "type";
var RESOURCE_ID = "res_id";
var URL_resource_detail = "/conveyor/plans/get_resource_detail";
$cancel_clone = function() {
	var plan_id = $("#id_plan_id").val();
	$.ajaxSetup({async: false});
	$.ajaxSetup({beforeSend: function(xhr, settings){xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));}});
	$.post('/conveyor/plans/' + plan_id + "/cancel", function(json){});
}

$(function(){
	$("input[type='submit'][name='clone']").click(function(){
		$("input#id_action_type").val("clone");
		$("div.clone-destination-dialog").find(".modal-footer").css({"margin-left":"0px", "margin-right": "0px"});
		left = ($("form#plan_topology_form").width() - $("div.clone-destination-dialog").width()) / 2;
		$("div.clone-destination-dialog").css({"display": "block", "position": "fixed", "left": left+"px", "top": "30px"});
		return false;
	});
	$("input[type='submit'][name='migrate']").click(function(){
		$("input#id_action_type").val("migrate");
		$("div.clone-destination-dialog").find(".modal-footer").css({"margin-left":"0px", "margin-right": "0px"});
		left = ($("form#plan_topology_form").width() - $("div.clone-destination-dialog").width()) / 2;
		$("div.clone-destination-dialog").css({"display": "block", "position": "fixed", "left": left+"px", "top": "30px"});
		return false;
	});
	$("input[type='submit'][name='save']").click(function(){
		$("input#id_action_type").val("save");
	})
	if($("a.btn.cancel").length && $("a.btn.cancel").attr("is_new") == "True") {
		$("input#id_action_type").val("cancel");
		$("a.btn.cancel").click($cancel_clone);
		$("div.modal-header").find('a.close').click($cancel_clone);
	}
})

/* The type of item in src or update must be String Array
 * Object(here is Dictionary)*/
function arr_merge(src, update) {
    if(src === null || typeof src === "undefined") {return update;}
	if (update === null || typeof update === "undefined") {return src;}
	for(var index in update) {
		value = update[index]
		if('[object Array]' == Object.prototype.toString.call(value)){
			src[index] = arr_merge(src[key], update);
		}else if((typeof obj=='object') && obj.constructor==Object) {
			src[index] = dict_merge(src[key], update[key]);
		}else {
			src[index] = value;
		}
	}
	return src;
}
/* The type of values in src or update must be String Array
 * Object(here is Dictionary)*/
function dict_merge(src, update){
	if(src === null || typeof src === "undefined") {return update;}
	if (update === null || typeof update === "undefined") {return src;}
	for(var key in update){
		value = update[key]
		if('[object Array]' == Object.prototype.toString.call(value)){
			src[key] = arr_merge(src[key], update);
		}else if((typeof obj=='object') && obj.constructor==Object) {
			src[key] = dict_merge(src[key], update[key]);
		}else {
			src[key] = value;
		}
	}
	return src;
}
    
var table_info = "div#resource_info_box";
var detailinfo_table = "table.detailInfoTable";
var detailinfo_div = "div.detailInfoCon"
var cancel_actions = ["a.closeTopologyBalloon", "button.cancel"];
var save_actions = ["button.save-info"]
var ori_clone_plan = "#id_plan_resources";
var update_clone_plan = "div#update_clone_plan_data";
var update_resources_input = "input#id_update_resource";
var update_resource_input = "input#id_update_resources";
var updated_resources_input = "input#id_updated_resources";
var dependencies_input = "input#id_dependencies";

function get_update_resource(resource_type, resource_id){
	var data_from = $(update_resources_input).val();
	var data_from = eval('(' + data_from + ')');
	for(var index in data_from) {
		update = data_from[index];
		if(update.type === resource_type && update.res_id === resource_id){
			return update;}
	}
	return {};
}

function get_update_resources(){
	var data_from = $(update_resources_input).val();
	var data_from = eval('(' + data_from + ')');
	for(var index in data_from) {
		update = data_from[index];
		if(update.type === resource_type && update.res_id === resource_id){
			return update;}
	}
	return [];
}

function merge(dict1, dict2) {
	for(key in dict2) {
		dict1[key] = dict2[key];
	}
}

function save_changed_info(resource_type,resource_id, data) {
	var data_from = $(update_resources_input).val();
	var data_from = eval('(' + data_from + ')');
	for(var index in data_from) {
		update = data_from[index];
		if(update.type === resource_type && update.res_id === resource_id) {
			merge(update, data)
			$(update_resources_input).val(JSON.stringify(data_from));
			return;
		}			
	}
	data_from.push(data)
	$(update_resources_input).val(JSON.stringify(data_from));
}

function update_topology(json){
	//update d3 data element
    $("#d3_data").attr("data-d3_data", JSON.stringify(json));
    
    //update stack
    $("#stack_box").html(json.environment.info_box);
    set_in_progress(json.environment, json.nodes);
    needs_update = false;
    
    //Check Remove nodes
    remove_nodes(nodes, json.nodes);

    //Check for updates and new nodes
    json.nodes.forEach(function(d){
    	current_node = findNode(d.id);
        //Check if node already exists
        if (current_node) {
          //Node already exists, just update it
          current_node.status = d.status;

          //Status has changed, image should be updated
          if (current_node.image !== d.image){
            current_node.image = d.image;
            var this_image = d3.select("#image_"+current_node.id);
            this_image
              .transition()
              .attr("x", function(d) { return d.image_x + 5; })
              .duration(100)
              .transition()
              .attr("x", function(d) { return d.image_x - 5; })
              .duration(100)
              .transition()
              .attr("x", function(d) { return d.image_x + 5; })
              .duration(100)
              .transition()
              .attr("x", function(d) { return d.image_x - 5; })
              .duration(100)
              .transition()
              .attr("xlink:href", d.image)
              .transition()
              .attr("x", function(d) { return d.image_x; })
              .duration(100)
              .ease("bounce");
          }

          //Status has changed, update info_box
          current_node.info_box = d.info_box;

        } else {
          addNode(d);
          build_links();
        }
      });

      //if any updates needed, do update now
      if (needs_update === true){
        update();
      }
}

function get_update_plan_url(plan_id){
	return "/conveyor/plans/"+plan_id+"/update";
}

/* In dashboard, change resource's some propertity, them submit it to backend to
 * resolve.
 * params:
 * resource_type:	resource type in plan. like OS::Nova::Server.
 * resource_id:		resource id in plan. like server_0.
 * data:			data changed to resource.*/
function res_changed(resource_type, resource_id, data) {
	var plan_id = $("input#id_plan_id").val();
	var updated_resources = $(updated_resources_input).val();
	var dependencies = $(dependencies_input).val();
	var update_res = get_update_resource(resource_type, resource_id);
	$.ajaxSetup({beforeSend: function(xhr, settings){xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));}});
	var postdata = {"plan_id": plan_id, 
					"resource_type": resource_type, 
					"resource_id": resource_id,
					"updated_resources": updated_resources,
					"dependencies": dependencies,
					"update_resource": update_res,
					"data": JSON.stringify(data)}
	jQuery.post(get_update_plan_url(plan_id), postdata,function(json){
		update_topology(JSON.parse(json.d3_data));
		for(index in json.update_resources) {
			item = json.update_resources[index];
			save_changed_info(item.type,item.res_id, item);
		}
		$(updated_resources_input).val(JSON.stringify(json.updated_resources));
		$(dependencies_input).val(JSON.stringify(json.dependencies));
	 });
}

function compare_ip(ipBegin, ipEnd)  
{  
    temp1 = ipBegin.split(".");
    temp2 = ipEnd.split(".");
    for (i = 0; i < 4; i++){
    	j = parseInt(temp1[i]);k = parseInt(temp2[i])
    	if (j>k){
    		return 1;
    	}else if (j<k){
    		return -1;
    	}
    }
    return 0;     
}

function ip_check_in_cidr(alloc, ip) {
	try{
		for(index in alloc){if(compare_ip(alloc[index].start, ip) <= 0 && compare_ip(ip, alloc[index].end) <= 0) { return true; }}
		return false;
	} catch(e) {return false;}
	
}

function clear_editing() {
	$("image[editing=true]").each(function(){
		$(this).attr({"href": $(this).attr("ori-href"), "editing": false});
	});
}

$hide_table_info = function() {$(table_info).html("");$(table_info).css("display", "none"); clear_editing(); return false;};
var is_updating = false;

/*Save the change information of detail resource.*/
$save_table_info = function() {
	try{
		if(is_updating){return false;}
		is_updating = true;
		var resource_type = $(detailinfo_div).attr("resource_type");
		var resource_id = $(detailinfo_div).attr("resource_id");
		var data = {"type": resource_type, "res_id": resource_id};
		if(resource_type === 'OS::Nova::Server'){
			var user_data = $("#user_data").val();
			ori_user_data = $("#user_data").attr("data-ori");
			if(user_data != ori_user_data) {
				data["user_data"] = user_data;
			}
			if($("div#resource_info_box table#metadatas").length){
				t_md = $("div#resource_info_box table#metadatas");
				if(typeof($(t_md).attr("deleted_ids"))!="undefined" || $(t_md).find("tr[data_from=client]").length){
					metadata = [];
					$(t_md).find("tbody tr:not(.new-row):not(.empty)").each(function(){
						key = $(this).attr("data-object-id");
						value = $(this).find("td:last").text();
						metadata.push('"' + $.trim(key) + '":"' + $.trim(value) + '"');
					})
					data["metadata"] = JSON.parse("{"+metadata.join(",")+"}");
				}
			}
			if(data.length == 2){return false;}
		} else if(resource_type == "OS::Nova::KeyPair") {
			var ori_keypair = $("select[name=keypairs]").attr("data-ori"); var keypair = $("select[name=keypairs]").val();
			if(ori_keypair == keypair) {
				return false;
			}
			data["name"] = keypair;
			res_changed(resource_type, resource_id, data);
		} else if(resource_type === "OS::Neutron::Net") {
			sel_net_id = $("select[name=networks]").val(); ori_net_id = $("select[name=networks]").attr("data-ori");
			if(sel_net_id == ori_net_id) {
				return false;
			}
			data["id"] = sel_net_id;
			res_changed(resource_type, resource_id, data);
		} else if(resource_type === "OS::Neutron::Port") {
			var changed = false;
			var fixed_ips = []
			$("input.ip").each(function(){
				ori_ip = $(this).attr("data-ori");ip=$(this).val();
				var alloc = JSON.parse($(this).attr("data-alloc"));
				if(! ip_check_in_cidr(alloc, ip)) {
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
			ori_subnet_id = $("select[name=subnets]").attr("data-ori");sel_subnet_id =$("select[name=subnets]").val();
			if(ori_subnet_id == sel_subnet_id) {
				return false;
			}
			data["id"] = sel_subnet_id;
			res_changed(resource_type, resource_id, data);
		} else if(resource_type == "OS::Neutron::SecurityGroup") {
			ori_sg_id = $("select[name=sgs]").attr("data-ori");sel_sg_id = $("select[name=sgs]").val();
			if(ori_sg_id != "" && ori_sg_id != sel_sg_id) {
				alert("ori_sg_id:"+ori_sg_id+",sel_sg_id"+sel_sg_id)
				data["id"] = sel_sg_id;
			}
			if($("div#resource_info_box table#rules").length){
				t_rules = $("div#resource_info_box table#rules");
				if(typeof($(t_rules).attr("deleted_ids"))!="undefined"){
					data["del_rule_ids"] = $(t_rules).attr("deleted_ids");
				}
			}
			if(data.length == 2){return false;}
			res_changed(resource_type, resource_id, data);
		} else if(resource_type == "OS::Neutron::FloatingIP") {
			ori_fip_id = $("select[name=fips]").attr("data-ori");sel_fip_id = $("select[name=fips").val();
			if(ori_fip_id == sel_fip_id) {return false;}
			data["id"] = sel_fip_id;
			res_changed(resource_type, resource_id, data);
		} else { return false; }
		save_changed_info(resource_type, resource_id, data);
		$(table_info).html("");$(table_info).css("display", "none");
		clear_editing();
		return false; 
	} catch(err){
		alert(err)
	} finally{
		is_updating = false;
		return false;
	}
}

$node_click = function(){
	clear_editing();
	var plan_id = $("input#id_plan_id").val();
	var is_original = $("div#is_original").attr("data-is_original")
	var node_id = $(this).attr("node_id");
	var node_type = $(this).attr("node_type");
	var update_data = get_update_resource(node_type, node_id);
	var updated_res = $("#id_updated_resources").val();
	$.ajaxSetup({beforeSend: function(xhr, settings){xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));}});
	var postdata = {"plan_id": plan_id, "resource_type": node_type, "resource_id": node_id, "update_data": JSON.stringify(update_data), "updated_res": updated_res, "is_original": is_original}
	jQuery.post(URL_resource_detail,postdata,function(data){
		if(data.msg !== "success") {
			return false;
		}
		$("image#"+node_id).attr("href", data.image);
		click_img = data.image
		if(click_img != "") {
			$("image[id=image_"+node_id+"]").attr("ori-href", $("image[id=image_"+node_id+"]").attr("href"));
			$("image[id=image_"+node_id+"]").attr({"href": click_img, "editing": true});
		}
		$("#resource_info_box").html(data.data).css("display", "block");
	 });
};

function hide_clone_des(){
	$("div.clone-destination-dialog").hide();
}

$(function(){
	for (action in cancel_actions) { $(cancel_actions[action]).click($hide_table_info);}
	for (action in save_actions) { $(save_actions[action]).click($save_table_info); }
	if($("input[name=clone][type=submit]").length){$("g.node").click($node_click);}
})

$(function(){
	if($("div.btn.btn-primary.clone_plan").length) {
		$("div.btn.btn-primary.clone_plan").click(function(){
			$("form#plan_topology_form").submit();
		});
		$("div.clone-destination-dialog a#close_save_plan_dialog").click(function(){$("div.clone-destination-dialog").hide();});
	}
})

///////////////////////////////////////////////////////////////////////////////
/* For resource detail. Allow to add some items for property with type of list
 * of detail resource.
 * params:
 * t_seletor: 			js selector of the table being to operate.
 * t_type: 				the type (or name) of table. like: metadatas, rules
 * add_action_selector: js selector of the add action button.*/
function open_add_operation(t_selector, t_type, add_action_selector){
 	if($(add_action_selector).length){
		$(add_action_selector).click(function(){
			if(t_type == "metadatas"){
				if(!$(t_selector).find("tr.new-row").length){
					$(t_selector).find("tbody").prepend('<tr class="new-row"><td class="multi_select_column"><td class="sortable normal_column"><input name="key" class="form-control" onkeydown="if(event.keyCode==13){add_md_for_server(\'table#metadatas\')};"/></td><td class="sortable normal_column"><input name="value" class="form-control" onkeydown="if(event.keyCode==13){add_md_for_server(\'table#metadatas\')};"/></td></tr>')	
				}
			}else if(t_type == "rules"){
				if($("#resource_info_box form#create_security_group_rule_form").length){return;}
				$.get("/project/access_and_security/security_groups/"+$("select[name=sgs]").val()+"/add_rule/", function(rsp){
					form = $(rsp).find("form#create_security_group_rule_form")
					$(form).append($(form).find("div.col-sm-6:first").html()).find("div.modal-body").remove();
					$(form).find("div.modal-footer").css("width", "360px")
					$("#resource_info_box div.footer").before($(form).prop("outerHTML"));
				});
				return false;
			}
		});
	}
}

/* For resource detail. All to delete some items for property with type of list
 * of detail resource.
 * params:
 * t_seletor:			js selector of the table being to operate.
 * del_action_selector: js selector of the delete action button.*/
function open_delete_operation(t_seletor, del_action_selector){
	if($(rm_action).length){$(rm_action).click(function(){rm_table_items(t_seletor, rm_action);return false;});}
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
}

/* Remove items for table temporary. while not delete behind*/
/* params:
 * t_selector:			the css selector of the table being to operate.
 * del_action_selector: js selector of the delete action button.*/
function rm_table_items(t_selector, del_action_selector){
	$(t_selector).find("tbody tr").each(function(){
		if($(this).find("input[name=object_ids].table-row-multi-select").attr("checked")=="checked"){
			item_id = $(this).attr("data-object-id");
			if(typeof($(t_selector).attr("deleted_ids"))=="undefined"){$(t_selector).attr("deleted_ids", item_id);}
			else{$(t_selector).attr("deleted_ids", $(t_selector).attr("deleted_ids") + " " + item_id);}
			$(this).remove();
		}
	});
	if(!$(del_action_selector).hasClass("disabled")){$(del_action_selector).addClass("disabled");}
}

/* For resource detail. Add an new metadata item for instance metadata property.
 * params:
 * t_selector: js selector of metadata table.*/
function add_md_for_server(t_seletor){
	in_key = $(t_seletor).find("tbody tr.new-row input[name=key]");
	in_value = $(t_seletor).find("input[name=value]");
	key = $(in_key).val();
	value = $(in_value).val();
	if(key==""){$(in_key).focus();return;}
	if(value==""){$(in_value).focus();return;}
	row = '<tr data_from="client" data-object-id="' + key + '" id="metadatas__row__' + key + '">'
	      + '<td class="multi_select_column"><input class="table-row-multi-select" name="object_ids" type="checkbox" value="' + key + '"></td>'
	      + '<td class="sortable normal_column">' + key + '</td>'
	      + '<td class="sortable normal_column">' + value + '</td></tr>'
    $(t_seletor).find("tr.new-row").remove();
	$(t_seletor).find("tbody").prepend(row);
}

function add_rule_for_sg(t_select){
	
}

/* For resource detail. When security_group_id changed, than change the content
 * of rules related to secgroup.
 * params:
 * sg_id:		security_group_id.
 * rt_selector: js selector of rules table.*/
function update_sg_rules(sg_id, rt_selector){
	$.get("plans/get_secgroup_rules/" + sg_id, function(rsp){
		$(rt_selector).find(".table_wrapper").replaceWith(rsp);
		table = "#resource_info_box table#rules"
		add_action = "#rules__action_add_rule";
		rm_action = "#rules__action_delete_rule";
		open_add_operation(table, "rules", add_action);
		open_delete_operation(table, rm_action);
	});
}

/* For resource detail. Show an rule table for user to edit, and then add it to 
 * related secgroup rules.*/
function new_rules_table(){
	if($("#resource_info_box form#create_security_group_rule_form").length){return;}
	$.get("/project/access_and_security/security_groups/"+$("select[name=sgs]").val()+"/add_rule/", function(rsp){
		form = $(rsp).find("form#create_security_group_rule_form")
		$(form).append($(form).find("div.col-sm-6:first").html()).find("div.modal-body").remove();
		$(form).find("div.modal-footer").css("width", "360px")
		$("#resource_info_box div.footer").before($(form).prop("outerHTML"));
	});
	return false;
}