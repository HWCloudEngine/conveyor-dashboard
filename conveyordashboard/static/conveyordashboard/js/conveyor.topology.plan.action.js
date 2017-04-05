$cancel_clone = function() {
	if($(this).attr("id") == "close_plan_dest_dialog") {return false;}
	var plan_id = $("#id_plan_id").val();
	$.ajaxSetup({async: false});
	$.ajaxSetup({beforeSend: function(xhr, settings){xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));}});
	$.post(getPrefixUrl() + "conveyor/plans/" + plan_id + "/cancel", function(json){});
};

/*
* For clone plan*/
$(function(){
	var clone_ipt=$("input[type='submit'][name='clone']");
	if(clone_ipt.length){
		clone_ipt.click(function(){
			$("input#id_action_type").val("clone");
			var clone_dest_dialog = $("div.plan-destination-dialog");
			$(clone_dest_dialog).find(".modal-footer").css({"margin-left":"0px", "margin-right": "0px"});
			var left = ($("form#plan_topology_form").width() - $(clone_dest_dialog).width()) / 2;
			$(clone_dest_dialog).css({"display": "block", "position": "fixed", "left": left+"px", "top": "30px"});
			return false;
		});
		$("input[type='submit'][name='save']").click(function(){
			$("input#id_action_type").val("save");
			var spd=$("div.save-plan-dialog");
			spd.find(".modal-footer").css({"margin-left":"0px", "margin-right": "0px"});
			var left = ($("form#plan_topology_form").width() - $(spd).width()) / 2;
			spd.css({"display": "block", "position": "fixed", "left": left+"px", "top": "30px"});
			return false;
		});
		$("g.node").click($node_click);
	}

	var clone_node = $("div.clone_plan");
	if(clone_node.length) {
		clone_node.click(function(){
			$("form#plan_topology_form").submit();
		});
	}
	var save_node = $("div.save_plan");
	if(save_node.length){
		save_node.click(function () {
			$("form#plan_topology_form").submit();
		});
	}
});

/*
* For migrate plan*/
$(function(){
	var migrate_ipt = $("input[type='submit'][name='migrate']");
	if(migrate_ipt.length) {
		migrate_ipt.click(function () {
			var plan_dest_node = $("div.plan-destination-dialog");
			$("input#id_action_type").val("migrate");
			$(plan_dest_node).find(".modal-footer").css({"margin-left":"0px", "margin-right": "0px"});
			var left = ($("form#plan_migrate_form").width() - $(plan_dest_node).width()) / 2;
			$(plan_dest_node).css({"display": "block", "position": "fixed", "left": left+"px", "top": "30px"});
			return false;
		});
		$("input[type='submit'][name='save']").click(function(){
			$("input#id_action_type").val("save");
			$("form#plan_migrate_form").submit();
		});
		$("g.node").click(function () {
			return false;
		});
	}

	var migrate_node = $("div.migrate-plan");
	if(migrate_node.length) {
		$(migrate_node).click(function(){
			$("form#plan_migrate_form").submit();
		});
	}
});

/*
* Cancel plan*/
$(function () {
	var cancel_btn = $("a.btn.cancel");
	if(cancel_btn.length && cancel_btn.attr("is_new") == "True") {
		cancel_btn.click($cancel_clone);
		$("div.modal-header").find('a.close').click($cancel_clone)
	}

	$("a#close_plan_dest_dialog").click(function(){$("div.plan-destination-dialog").hide();return false;});
	$("a#close_save_plan_dialog").click(function(){$("div.save-plan-dialog").hide();return false;});
});
