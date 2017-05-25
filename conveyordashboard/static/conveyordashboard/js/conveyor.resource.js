/**
 * Copyright 2017 Huawei, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

"use strict";

var fieldTypes = {
  ipt: 'input',
  chk: 'checkbox',
  slt: 'select',
  sfo: 'selectFromOther',
  meta: 'metadata',
  spec: 'spe'
};

var conveyorResources = {
  resources: {
    'OS::Nova::Server': {
      user_data: {fieldType: fieldTypes.ipt},
      metadata: {fieldType: fieldTypes.meta}
    },
    'OS::Nova::KeyPair': {
      keypairs: {fieldType: fieldTypes.sfo}
    },
    'OS::Cinder::Volume': {
      name: {fieldType: fieldTypes.ipt},
      size: {fieldType: fieldTypes.ipt},
      descript: {fieldType: fieldTypes.ipt},
      copy_data: {fieldType: fieldTypes.chk},
      volumes: {fieldType: fieldTypes.sfo},
      metadata: {fieldType: fieldTypes.meta}
    },
    'OS::Cinder::VolumeType': {
      volumetypes: {fieldType: fieldTypes.sfo}
    },
    'OS::Cinder::Qos': {
      qoss: {fieldType: fieldTypes.sfo}
    },
    'OS::Neutron::Net': {
      name: {fieldType: fieldTypes.ipt},
      shared: {fieldType: fieldTypes.chk},
      admin_state_up: {fieldType: fieldTypes.slt},
      networks: {fieldType: fieldTypes.sfo},
      value_specs: {
        fieldType: fieldTypes.spec,
        specFunc: function (field, data) {
          var valueSpecs = {};
          var modified = false;
          var seg_node = $("#id_segmentation_id");
          if(seg_node.length == 1) {
            valueSpecs["segmentation_id"] = $(seg_node).val();
            if($(seg_node).attr("data-ori") != $(seg_node).val()) {
              modified = true;
            }
          }
          var phy_net_node = $("#id_physical_network");
          if(phy_net_node.length == 1) {
            valueSpecs["physical_network"] = $(phy_net_node).val();
            if($(phy_net_node).attr("data-ori") != $(phy_net_node).val()) {
              modified = true;
            }
          }
          var net_type_node = $("#id_network_type");
          if(net_type_node.length==1) {
            valueSpecs["network_type"] = $(net_type_node).val();
            if($(net_type_node).attr("data-ori") != $(net_type_node).val()) {
              modified = true;
            }
          }
          var router_external_node = $("#id_router_external");
          if(router_external_node.length==1) {
            valueSpecs["router_external"] = $(router_external_node).val()
          }
          if(modified) {
            data[field] = valueSpecs;
          }
        }
      }
    },
    'OS::Neutron::Subnet': {
      name: {fieldType: fieldTypes.ipt},
      cidr: {
        fieldType: fieldTypes.ipt,
        validate: function (field, data) {
          var cidr_node=$("input#id_cidr");
          var cidr=$(cidr_node).val();
          if(!conveyorUtil.checkCidr(cidr, 31)) {
            $(cidr_node).focus();
            return false
          }
          return true;
        }
      },
      gateway_ip: {fieldType: fieldTypes.ipt},
      no_gateway: {fieldType: fieldTypes.chk},
      enable_dhcp: {fieldType: fieldTypes.chk},
      allocation_pools: {fieldType: fieldTypes.ipt},
      dns_nameservers: {fieldType: fieldTypes.ipt},
      host_routes: {fieldType: fieldTypes.ipt},
      subnets: {fieldType: fieldTypes.sfo}
    },
    'OS::Neutron::Port': {
      fixed_ips: {
        fieldType: fieldTypes.spec,
        specFunc: function (field, data) {
          var changed = false;
          var fixed_ips = [];
          $("input.ip").each(function(){
            var ori_ip = $(this).attr("data-ori");
            var ip=$(this).val();
            var alloc = $.parseJSON($(this).attr("data-alloc"));
            if(! conveyorUtil.ipCheckInCidr(alloc, ip)) {
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
        }
      }
    },
    'OS::Neutron::FloatingIP': {
      fips: {fieldType: fieldTypes.sfo}
    },
    'OS::Neutron::Router': {
      name: {fieldType: fieldTypes.ipt},
      admin_state_up: {fieldType: fieldTypes.slt},
      routers: {fieldType: fieldTypes.sfo}
    },
    'OS::Neutron::SecurityGroup': {
      secgroups: {fieldType: fieldTypes.sfo},
      rules: {
        fieldType: fieldTypes.spec,
        specFunc: function (field, data) {
          var sgr_node = $("#id_sgrs");
          if(sgr_node.length){
            var rules = $(sgr_node).attr("data-ori");
            var t_rules = $("div#resource_info_box table#rules");
            if($(t_rules).length){
              if(typeof($(t_rules).attr("deleted_ids"))!="undefined"){
                var json_rs = $.parseJSON(rules);
                var deleted_r_ids = $(t_rules).attr("deleted_ids").split(' ');
                for(var index in deleted_r_ids){
                  var id = deleted_r_ids[index];
                  for(var r in json_rs){
                    if(json_rs[r]['id'] == id){json_rs.splice(r, 1);break;}
                  }
                }
                data["rules"] = JSON.stringify(json_rs);
              }else if($(sgr_node).attr('changed') == "true"){
                data["rules"] = rules
              }
            }else if($(sgr_node).attr('changed') == "true"){
              data["rules"] = rules
            }
          }
        }
      }
    },
    'OS::Neutron::Vip': {
      name: {fieldType: fieldTypes.ipt},
      protocol_port: {fieldType: fieldTypes.ipt},
      connection_limit: {fieldType: fieldTypes.ipt},
      address: {fieldType: fieldTypes.ipt},
      admin_state_up: {fieldType: fieldTypes.slt}
    },
    'OS::Neutron::Pool': {
      name: {fieldType: fieldTypes.ipt},
      protocol_port: {fieldType: fieldTypes.ipt},
      admin_state_up: {fieldType: fieldTypes.slt},
      lb_method: {fieldType: fieldTypes.slt}
    },
    'OS::Neutron::PoolMember': {
      address: {fieldType: fieldTypes.ipt},
      protocol_port: {fieldType: fieldTypes.ipt},
      weight: {fieldType: fieldTypes.ipt},
      admin_state_up: {fieldType: fieldTypes.slt}
    },
    'OS::Neutron::HealthMonitor': {
      delay: {fieldType: fieldTypes.ipt},
      max_retries: {fieldType: fieldTypes.ipt},
      timeout: {fieldType: fieldTypes.ipt},
      admin_state_up: {fieldType: fieldTypes.slt},
      type: {fieldType: fieldTypes.slt}
    },
    'OS::Neutron::Listener': {
      protocol_port: {type: fieldTypes.ipt},
      protocol: {type: fieldTypes.slt}
    }
  },
  processs: function (resType, resId) {
    var self = this;
    var data = {};
    var needPosted = false;

    try {
      var resource = self.resources[resType];
    } catch (e) {
      console.error(e);
      return null
    }

    $.each(resource, function (field, value) {
      // Check this field need to validate or not
      if($.inArray('validate', Object.keys(value)) >= 0) {
        if(!value.validate(field, value)) {
          return null
        }
      }
      if(value.fieldType == fieldTypes.ipt) {
        self.getInputData(field, data);
      } else if (value.fieldType == fieldTypes.chk) {
        self.getChkData(field, data)
      } else if (value.fieldType == fieldTypes.slt) {
        self.getSelectData(field, data);
      } else if (value.fieldType == fieldTypes.sfo) {
        if(self.getDataFromExisted(field, data)) {needPosted = true;}
      } else if (value.fieldType == fieldTypes.meta) {
        self.getMetaTableData(field, data);
      } else if(value.fieldType == fieldTypes.spec) {
        value.specFunc(field, data);
      }
    });
    return {data: data, needPosted: needPosted}
  },
  /*
   * Check input field(textbox, select) data is changed, if yes, update it to dstDict
   */
  getInputData: function (field, dstDict) {
    var selector = '#id_' + field;
    var inputEle = $(selector);
    if(inputEle.length === 0) {
      return false;
    }
    if($(inputEle).attr("data-ori") != $(inputEle).val()) {
      dstDict[field] = $(inputEle).val();
      return true;
    }
    return false;
  },
  /*
   * Check input field(checkbox) data is changed, if yes, update it to dstDict
   */
  getChkData: function (field, dstDict) {
    var selector = '#id_' + field;
    var chkEle = $(selector);
    if(chkEle.length === 0) {
      return false;
    }
    var checked = $(chkEle).is(':checked');
    if($(chkEle).attr('data-ori') != checked) {
      dstDict[field] = checked;
      return true;
    }
    return false;
  },
  getSelectData: function (field, dstDict) {
    var selector = 'select[name=' + field + 's]';
    var inputEle = $(selector);
    if(inputEle.length === 0) {
      return false;
    }
    if($(inputEle).attr('data-ori') != $(inputEle).val()) {
      dstDict[field] = $(inputEle).val();
      return true;
    }
    return false;
  },
  /* Change resource from ori to other res
   * params
   * field: generally, it is the sort resource type, link volume, net
   * dstDict:  */
  getDataFromExisted: function (field, dstDict) {
    var selector = '[name=' + field + ']';
    var slt_node = $(selector);
    if(slt_node.length === 0) {
      return false;
    }
    if($(slt_node).val() != $(slt_node).attr('data-ori')) {
      dstDict['id'] = $(slt_node).val();
      return true;
    }
    return false;
  },
  getMetaTableData: function (field, dstDict) {
    var metaTable = $('div#resource_info_box table#' + field + 's');
    if(metaTable.length == 0) {
      return false;
    }

    if(typeof $(metaTable).attr('deleted_ids') != 'undefined' || $(metaTable).find('tr[data_from=client]').length) {
      var metadata = [];
      $(metaTable).find("tbody tr:not(.new-row):not(.empty)").each(function () {
        var key = $(this).attr('data-object-id');
        var value = $(this).find('td:last').text();
        metadata.push('"' + $.trim(key) + '":"' + $.trim(value) + '"');
      });
      dstDict['metadata'] = $.parseJSON("{"+metadata.join(",")+"}");
      return true;
    }
    return false;
  }
};
