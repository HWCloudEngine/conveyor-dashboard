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

var conveyorProjectOverview = {
  t_ids: {},
  tag_clone_plan_action: 'a.create-clone-plan-for-mul-sel',
  tag_migrate_plan_action: 'a.create-migrate-plan-for-mul-sel',
  checkTopologyLink: function () {
    var self = this;
    var t_ids = self.t_ids;
    var len = 0;
    var index;
    $.each(t_ids, function (k, v) {
      len += v.length
    });
    var actions = [self.tag_clone_plan_action, self.tag_migrate_plan_action];
    for (index = 0; index < actions.length; index++) {
      var action = actions[index];
      if ($(action).length == 0) {
        return;
      }
      if (len > 0) {
        if ($(action).hasClass("disabled")) {
          $(action).removeClass("disabled");
        }
      } else {
        if (!$(action).hasClass("disabled")) {
          $(action).addClass("disabled");
        }
      }
    }
  },
  getQueryString: function () {
    var self = this;
    var t_ids = self.t_ids;
    var id_strs = [];
    $.each(t_ids, function (k, v) {
      if (v.length > 0) {
        id_strs.push(k + "*" + v.join(","));
      }
    });
    var url = id_strs.join("**");
    return '?ids=' + url;
  },
  checkAllOfOneType: function (obj) {
    var self = this;
    var table = $('#resource');
    var this_id = obj.id;
    var child_cls = '.child-of-' + this_id;
    $(obj).find('td:eq(0) input').click(function () {
      var type = $.trim($(obj).find('td:eq(1)').html());
      if ($(this).attr('checked') == 'checked') {
        if ($(obj).hasClass('collapsed')) {
          $(obj).find('td:eq(0) span').click()
        }
        var children = table.find(child_cls);
        if ($(children).length) {
          var tmp_ids = [];
          $(children).each(function () {
            $(this).find('td:eq(0) input').attr('checked', 'checked');
            tmp_ids.push($(this).attr('data-object-id'));
          });
          self.t_ids[type] = tmp_ids;
        }
      }
      else {
        $(table.find(child_cls)).each(function () {
          $(this).find('td:eq(0) input').removeAttr('checked');
        });
        self.t_ids[type] = [];
      }
      self.checkTopologyLink();
    });

  },
  prepareAction: function () {
    var self = this;
    var t_ids = self.t_ids;
    var table = $('#resource');
    var type = '';
    table.find('tbody tr').each(function () {
      var tr = this;
      if ($(this).hasClass('parent')) {
        var this_id = this.id;
        var child_cls = '.child-of-' + this_id;
        if (this_id.indexOf('node--1-') == 0) {
          $(this).find('td:eq(0) input').click(function () {
            if ($(this).attr('checked') == 'checked') {
              table.find(child_cls).each(function () {
                var chk = $(this).find('td:eq(0) input');
                if ($(chk).attr('checked') != 'checked') {
                  $(chk).click()
                }

              });
            }
            else {
              table.find(child_cls).each(function () {
                var chk = $(this).find('td:eq(0) input');
                if ($(chk).attr('checked') == 'checked') {
                  $(chk).click()
                }
              });
            }
          });
        } else if (this_id.indexOf('node--2-') == 0) {
          return self.checkAllOfOneType(this);
        }
      } else {
        var res_id = $(this).attr('data-object-id');
        $(tr).find('td:eq(0) input').click(function () {
          type = $.trim($(tr).find('td:eq(3)').html());
          if ($(this).attr('checked') == 'checked') {
            try {
              if ($.inArray(res_id, t_ids[type]) == -1) {
                t_ids[type].push(res_id);
              }
            } catch (e) {
              console.log(e);
              t_ids[type] = [res_id]
            }
          } else {
            var index = $.inArray(res_id, t_ids[type]);
            if (index != -1) {
              t_ids[type].splice(index, 1);
            }
          }
          self.checkTopologyLink();
        });
      }
    });
  },
  checkBox: function (value, labelFor) {
    var chkId = conveyorUtil.randomString(10);
    return '<div class="themable-checkbox" style="display: inline-block;"><input class="table-row-multi-select" id="' + chkId + '" name="object_ids" type="checkbox" value="' + value + '"><label for="' + chkId + '"><span>' + labelFor + '</span></label></div>'
  },
  init: function () {
    var self = this;
    var ori = $('#hide_ori_data');
    var table_wrapper = ori.find('.table_wrapper')[0];
    var table = $(table_wrapper).find('table');
    table.find('thead tr.tablesorter-headerRow th:eq(0)').empty();
    var t_type = {};
    $(table).find('tbody tr').each(function () {
      var tenant = $.trim($(this).find('td:eq(1)').html());
      var type = $(this).find('td:eq(3)').html();
      try {
        if (t_type[tenant].toString().indexOf(type) == -1) {
          t_type[tenant].push(type);
        }
      } catch (e) {
        t_type[tenant] = [type]
      }
    });
    $.each(t_type, function (tenant, types) {
      $(table).find('tbody').prepend("<tr id='node--1-" + tenant + "' class='parent'><td colspan='2'>" + self.checkBox('', tenant) + "</td><td>OS::Keystone::Project</td><td></td></tr>");
      for (var i = 0; i < types.length; i++) {
        var type = types[i];
        $(table).find('tbody tr#node--1-' + tenant).after("<tr id='node--2-" + (i + 1) + "' class='parent child-of-node--1-" + tenant + "'><td colspan='2'>" + self.checkBox('', type) + "</td><td>" + type + "</td><td></td></tr>");
        $(table).find('tbody tr').each(function () {
          if ($(this).find('td:eq(3)').html() == type) {
            $(this).addClass("child-of-node--2-" + (i + 1));
            $(table).find('tbody tr#node--2-' + (i + 1)).after($(this));
          }
        });
      }
    });
    $(table).treeTable();
    ori.before(table_wrapper);
    self.prepareAction();
    var actions = $(self.tag_clone_plan_action + ', ' + self.tag_migrate_plan_action);
    var btnTrigger = $('.btn-create-plan');
    $(actions).click(function () {
      var href = $(this).attr('href').split('?')[0];
      href += self.getQueryString();
      $(this).attr('href', href);
      $(this).trigger();
      return false;
    });
  }
};
