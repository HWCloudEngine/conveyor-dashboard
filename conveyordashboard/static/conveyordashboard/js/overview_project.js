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
  id_map: {},
  tag_create_plan: 'a.create-plan-with-multi-res',
  tag_project_plan_action: 'a.create-project-plan',
  checkTopologyLink: function () {
    var self = this;
    var t_ids = self.id_map;
    var len = 0;
    var index;
    $.each(t_ids, function (k, v) {
      len += v.length
    });
    var actions = [self.tag_create_plan];
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

    if ($('#resource thead input.table-row-multi-select').is(':checked')) {
      $(self.tag_project_plan_action).removeClass('disabled');
    } else {
      if (!$(self.tag_project_plan_action).hasClass("disabled")) {
          $(self.tag_project_plan_action).addClass("disabled");
        }
    }
  },
  getQueryString: function () {
    var project_id = $.trim($('#conveyor_project_id').text());
    var t_ids = this.id_map;
    var id_strs = [];
    $.each(t_ids, function (k, v) {
      if (v.length > 0) {
        id_strs.push(k + "*" + v.join(","));
      }
    });
    var url = id_strs.join("**");
    return '?plan_level=project:' + project_id + '&&ids=' + url;
  },
  typeIndex: function () {
    return $('#resource').find('thead th[data-selenium=res_type]').attr('data-column');
  },
  setParentTrChecked: function (childCls, parentCls) {
    var children = $(childCls);
    var checkParent = true;
    $(children).each(function (index, item) {
      if (!$(this).find('[type=checkbox]').is(':checked')) {
        checkParent = false;
      }
    });
    if (checkParent) {
      $(parentCls).find('[type=checkbox]').attr('checked', 'checked');
    }
  },
  checkAllOfOneType: function (tr) {
    var self = this;
    var table = $('#resource');
    var this_id = tr.id;
    var child_cls = '.child-of-' + this_id;
    var typeIndex = self.typeIndex();
    $(tr).find('td:eq(0) input').click(function () {
      var type = $.trim($(this).next().find('span').text());
      if ($(this).is(':checked')) {
        if ($(tr).hasClass('collapsed')) {
          $(tr).find('td:eq(0) span').click()
        }
        var children = table.find(child_cls);
        if ($(children).length) {
          var tmp_ids = [];
          $(children).each(function () {
            $(this).find('td:eq(0) input').attr('checked', 'checked');
            tmp_ids.push($(this).attr('data-object-id'));
          });
          self.id_map[type] = tmp_ids;
        }

        // If all of child node are checked, then the parent checkbox should be checked.
        self.setParentTrChecked('[id^="node--1-OS_"]', '#resource thead');
      }
      else {
        $(table.find(child_cls)).each(function () {
          $(this).find('td:eq(0) input').removeAttr('checked');
        });
        self.id_map[type] = [];

        // Remove the checked property of parent checkbox
        $('#resource thead th [type=checkbox]').removeAttr('checked');
      }
      self.checkTopologyLink();
    });

  },
  prepareAction: function () {
    var self = this;
    var table = $('#resource');
    var type = '';
    var typeIndex = self.typeIndex();
    table.find('thead th:eq(0) input[type=checkbox]').click(function () {
      var checked = $(this).is(':checked');
      if (checked) {
        table.find('tbody tr.parent').each(function (index, item) {
          var chk = $(this).find('td:eq(0) [type=checkbox]');
          if (!$(chk).is(':checked')) {
            $(chk).click();
          }
        });
      }
      else {
        table.find('tbody tr').each(function (index, item) {
          $(this).find('td:eq(0) [type=checkbox]').removeAttr('checked');
        });
        self.id_map = {};
        self.checkTopologyLink();
      }
    });
    table.find('tbody tr').each(function () {
      var tr = this;
      var t_ids = self.id_map;
      if ($(this).hasClass('parent')) {
        return self.checkAllOfOneType(this);
      } else {
        var res_id = $(this).attr('data-object-id');
        $(tr).find('td:eq(0) input').click(function () {
          type = $.trim($(tr).find('td:eq(' + typeIndex + ')').html());
          if ($(this).is(':checked')) {
            try {
              if ($.inArray(res_id, t_ids[type]) == -1) {
                t_ids[type].push(res_id);
              }
            } catch (e) {
              t_ids[type] = [res_id]
            }

            // If all of child node are checked, then the parent checkbox should be checked.
            var new_type = type.replace(/::/g, '__');
            var childCls = '.child-of-node--1-' + new_type;
            var parentCls = '#node--1-' + new_type;
            self.setParentTrChecked(childCls, parentCls);
            self.setParentTrChecked('[id^="node--1-OS_"]', '#resource thead');
          } else {
            var index = $.inArray(res_id, t_ids[type]);
            if (index != -1) {
              t_ids[type].splice(index, 1);
            }

            // Remove the checked property of parent checkbox
            $('#node--1-' + type.replace(/::/g, '__')).find('td:eq(0) [type=checkbox]').removeAttr('checked');
            $('#resource thead th [type=checkbox]').removeAttr('checked');
          }

          // Update creating plan searching string
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
    var typeIndex = self.typeIndex();
    var table_wrapper = ori.find('.table_wrapper')[0];
    var table = $(table_wrapper).find('table');
    var thead = table.find('thead');
    var columnLen = thead.find('th').length;
    thead.find('tr.tablesorter-headerRow th:eq(0)').empty().append(self.checkBox('', ''));
    var t_type = [];
    $(table).find('tbody tr').each(function () {
      var type = $.trim($(this).find('td:eq(' + typeIndex + ')').html());
      if ($.inArray(type, t_type) === -1) {
        t_type.push(type);
      }
    });
    $.each(t_type, function (index, type) {
      var new_type = type.replace(/::/g, '__');
      $(table).find('tbody').prepend("<tr id='node--1-" + new_type + "' class='parent'><td colspan='" + columnLen + "'>" + self.checkBox('', type) + "</td></tr>");
      $(table).find('tbody tr').each(function () {
        if ($.trim($(this).find('td:eq(' + typeIndex + ')').html()) == type) {
          $(this).addClass("child-of-node--1-" + (new_type));
          $(table).find('tbody tr#node--1-' + (new_type)).after($(this));
        }
      });
    });
    $(table).treeTable();

    // Display the resource table
    ori.before(table_wrapper);

    self.prepareAction();

    var actions = $(self.tag_create_plan);
    $(actions).click(function () {
      var href = $(this).attr('href').split('?')[0];
      href += self.getQueryString();
      $(this).attr('href', href);
      $(this).trigger();
      return false;
    });
  }
};
