var t_ids={};
var clone_plan_topology = "a.create-clone-plan-for-mul-sel";
var migrate_plan_topology = "a.create-migrate-plan-for-mul-sel";
var multi_sel_action=['#resource__action_create_plan_with_mul_res', '#resource__action_create_migrate_plan_with_mul_res'];
function check_topology_link(){
    var len = 0;
    var index;
    $.each(t_ids, function (k, v) {
       len+=v.length
    });
    for(index=0;index<multi_sel_action.length;index++) {
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
    $.each(t_ids, function (k, v) {
        if (v.length > 0) {
            id_strs.push(k+"*"+v.join(","));
        }
    });
    var url=id_strs.join("**");
    return '?ids='+url;
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
function check_all_of_one_type(obj) {
    var table = $('#resource');
    var this_id = obj.id;
    var child_cls='.child-of-'+this_id;
    $(obj).find('td:eq(0) input').click(function () {
        var type = $.trim($(obj).find('td:eq(1)').html());
        if($(this).attr('checked')=='checked'){
            if($(obj).hasClass('collapsed')){$(obj).find('td:eq(0) span').click()}
            var children=table.find(child_cls);
            if($(children).length){
                var tmp_ids=[];
                $(children).each(function () {
                     if($(this).find("td.actions_column .btn-clone").length > 0){
                         $(this).find('td:eq(0) input').attr('checked', 'checked');
                         tmp_ids.push($(this).attr('data-object-id'));
                     }
                });
                t_ids[type]=tmp_ids;
            }
        }
        else{
            $(table.find(child_cls)).each(function () {
                $(this).find('td:eq(0) input').removeAttr('checked');
            });
            t_ids[type]=[];
        }
        check_topology_link();
    });

}
function prepare_action() {
    var table = $('#resource');
    var type = '';
    table.find('tbody tr').each(function () {
        var tr = this;
        if($(this).hasClass('parent')){
            var this_id = this.id;
            var child_cls='.child-of-'+this_id;
            if(this_id.indexOf('node--1-')==0){
                $(this).find('td:eq(0) input').click(function () {
                    if($(this).attr('checked')=='checked'){
                        table.find(child_cls).each(function () {
                            var chk=$(this).find('td:eq(0) input');
                            if($(chk).attr('checked')!='checked'){$(chk).click()}

                        });
                    }
                    else{
                        table.find(child_cls).each(function () {
                            var chk=$(this).find('td:eq(0) input');
                            if($(chk).attr('checked')=='checked'){$(chk).click()}
                        });
                    }
                });
            }else if(this_id.indexOf('node--2-')==0){
                return check_all_of_one_type(this);
            }
        }else{
            var res_id = $(this).attr('data-object-id');
            $(tr).find('td:eq(0) input').click(function () {
                if($(tr).find("td.actions_column .btn-clone").length > 0){
                    type = $.trim($(tr).find('td:eq(3)').html());
                    if($(this).attr('checked')=='checked'){
                        try{
                            if($.inArray(res_id, t_ids[type]) == -1) {
                                t_ids[type].push(res_id);
                            }
                        }catch (e){
                            t_ids[type] = [res_id]
                        }
                    }else{
                        var index = $.inArray(res_id, t_ids[type]);
                        if(index != -1) {
                            t_ids[type].splice(index, 1);
                        }
                    }
                    check_topology_link();
                }
            });
        }
    });
}
$(function () {
    var ori = $('#hide_ori_data');
    var table_wrapper = ori.find('.table_wrapper')[0];
    var table = $(table_wrapper).find('table');
    table.find('thead tr.tablesorter-headerRow th:eq(0)').empty();
    var t_type={};
    $(table).find('tbody tr').each(function () {
        var tenant = $.trim($(this).find('td:eq(1)').html());
        var type=$(this).find('td:eq(3)').html();
        try{
            if(t_type[tenant].toString().indexOf(type)==-1){t_type[tenant].push(type);}
        }catch (e){
            t_type[tenant] = [type]
        }
    });
    $.each(t_type, function (tenant, types) {
        $(table).find('tbody').prepend("<tr id='node--1-"+tenant+"' class='parent'><td colspan='2'><input type='checkbox' value=''>"+tenant+"</td><td>OS::Keystone::Project</td><td></td></tr>");
        for(var i=0;i<types.length;i++){
            var type=types[i];
            $(table).find('tbody tr#node--1-'+tenant).after("<tr id='node--2-"+(i+1)+"' class='parent child-of-node--1-"+tenant+"'><td colspan='2'><input type='checkbox' value=''>"+type+"</td><td>"+type+"</td><td></td></tr>");
            $(table).find('tbody tr').each(function (){
            if($(this).find('td:eq(3)').html()==type){
                $(this).addClass("child-of-node--2-"+(i+1));
                $(table).find('tbody tr#node--2-'+(i+1)).after($(this));
            }
        });
        }
    });
    $(table).treeTable();
    ori.before(table_wrapper);
    prepare_action();
    if($(clone_plan_topology).length){$(clone_plan_topology).click($create_clone_plan_topology);}
    if($(migrate_plan_topology).length){$(migrate_plan_topology).click($create_migrate_plan_topology);}
});
