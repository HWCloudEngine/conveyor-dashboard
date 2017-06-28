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
  spec: 'spe'
};

var conveyorResources = {
  resources: {
    'OS::Nova::Server': {
      fields: {
        user_data: {fieldType: fieldTypes.ipt},
        metadata: {fieldType: fieldTypes.ipt}
      }
    },
    'OS::Nova::KeyPair': {
      fields: {
        keypairs: {fieldType: fieldTypes.sfo}
      }
    },
    'OS::Cinder::Volume': {
      fields: {
        name: {fieldType: fieldTypes.ipt},
        size: {fieldType: fieldTypes.ipt},
        descript: {fieldType: fieldTypes.ipt},
        copy_data: {fieldType: fieldTypes.chk},
        metadata: {fieldType: fieldTypes.ipt}
      }
    },
    'OS::Cinder::VolumeType': {
      fields: {
        volumetypes: {fieldType: fieldTypes.sfo}
      }
    },
    'OS::Cinder::Qos': {
      fields: {
        qoss: {fieldType: fieldTypes.sfo}
      }
    },
    'OS::Neutron::Net': {
      fields: {
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
      }
    },
    'OS::Neutron::Subnet': {
      fields: {
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
      }
    },
    'OS::Neutron::Port': {
      fields: {
        fixed_ips: {
          fieldType: fieldTypes.spec,
          specFunc: function (field, data) {
            var changed = false;
            var fixed_ips = [];
            $("input.ip").each(function(){
              var ori_ip = $(this).attr("data-ori");
              var ip=$(this).val();
              // var alloc = $.parseJSON($(this).attr("data-alloc"));
              // if(! conveyorUtil.ipCheckInCidr(alloc, ip)) {
              //   $(this).focus();
              //   return false;
              // }
              if(ori_ip != ip) {
                changed = true;
              }
              fixed_ips.push({"subnet_id": {"get_resource": $(this).attr("data-subnet-id")}, "ip_address": ip});
            });
            if(!changed) {return false;}
            data["fixed_ips"] = fixed_ips;
          }
        }
      }
    },
    'OS::Neutron::FloatingIP': {
      fields: {
        fips: {fieldType: fieldTypes.sfo}
      }
    },
    'OS::Neutron::Router': {
      fields: {
        name: {fieldType: fieldTypes.ipt},
        admin_state_up: {fieldType: fieldTypes.slt},
        routers: {fieldType: fieldTypes.sfo}
      }
    },
    'OS::Neutron::SecurityGroup': {
      fields: {
        secgroups: {fieldType: fieldTypes.sfo},
        rules: {
        fieldType: fieldTypes.spec,
        specFunc: function (field, data) {
          var sgr_node = $("#id_sgrs");
          if(sgr_node.length){
            var rules = $(sgr_node).attr("data-ori");
            var t_rules = $('.modal table#rules');
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
      }
    },
    'OS::Neutron::Vip': {
      fields: {
        name: {fieldType: fieldTypes.ipt},
        protocol_port: {fieldType: fieldTypes.ipt},
        connection_limit: {fieldType: fieldTypes.ipt},
        address: {fieldType: fieldTypes.ipt},
        admin_state_up: {fieldType: fieldTypes.slt}
      }
    },
    'OS::Neutron::Pool': {
      fields: {
        name: {fieldType: fieldTypes.ipt},
        protocol_port: {fieldType: fieldTypes.ipt},
        admin_state_up: {fieldType: fieldTypes.slt},
        lb_method: {fieldType: fieldTypes.slt}
      }
    },
    'OS::Neutron::PoolMember': {
      fields: {
        address: {fieldType: fieldTypes.ipt},
        protocol_port: {fieldType: fieldTypes.ipt},
        weight: {fieldType: fieldTypes.ipt},
        admin_state_up: {fieldType: fieldTypes.slt}
      }
    },
    'OS::Neutron::HealthMonitor': {
      fields: {
        delay: {fieldType: fieldTypes.ipt},
        max_retries: {fieldType: fieldTypes.ipt},
        timeout: {fieldType: fieldTypes.ipt},
        admin_state_up: {fieldType: fieldTypes.slt},
        type: {fieldType: fieldTypes.slt}
      }
    },
    'OS::Neutron::Listener': {
      fields: {
        protocol_port: {type: fieldTypes.ipt},
        protocol: {type: fieldTypes.slt}
      }
    }
  },
  process: function (resType, resId) {
    var self = this;
    var data = {};
    var needPosted = false;

    try {
      var resource = self.resources[resType];
    } catch (e) {
      console.error(e);
      return null
    }

    $.each(resource.fields, function (field, value) {
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
  }
};

/*
var plans = {
  '<plan_id>': {
    'ori_deps': [],
    'update_resources': []
  }
}

update_resource = {
  'original_id': 'This field keep the original id of plan resource.',
  'resource_type': 'The type of resource',
  'resource_id': 'This filed save the id of current resource',
  '...': 'The edit field'
}
*/
var conveyorPlan = {
  plans: {},
  dependentResMap: {
    'OS::Neutron::Net': ['OS::Neutron::Subnet', 'OS::Neutron::Port'],
    'OS::Neutron::Subnet': ['OS::Neutron::Port']
  },
  initPlan: function (planId, deps) {
    var oriDeps = [];
    var updateDeps = [];
    for(var idx in deps) {
      oriDeps.push($.extend({}, deps[idx]));
      updateDeps.push($.extend({}, deps[idx]));
    }
    this.plans[planId] = {
      'plan_id': planId,
      'ori_deps': oriDeps,
      'updated_deps': updateDeps,
      'update_resources': [],
      'replace_resources': []
    };
  },
  getPlan: function (planId) {
    try {
      return this.plans[planId];
    } catch (e) {
      return null;
    }
  },
  getUpdateResource: function (planId, resType, resId) {
    var plan = this.getPlan(planId);
    if (!plan) {
      return {};
    }
    var updateResources = plan.update_resources;
    for (var index in updateResources) {
      if (updateResources[index].resource_type == resType && updateResources[index].resource_id == resId) {
        return updateResources[index];
      }
    }
    return {};
  },
  updateUpdateResource: function (planId, resType, resId, data) {
    var plan = this.getPlan(planId);
    if (!plan) {
      return;
    }
    var updateResources = plan.update_resources;
    for (var index in updateResources) {
      if (updateResources[index].resource_type == resType && updateResources[index].resource_id == resId) {
        $.extend(true, updateResources[index], data);
        // conveyorUtil.merge(updateResources[index], data);
        return;
      }
    }
    updateResources.push($.extend({}, data, {resource_type: resType, resource_id: resId}));
  },
  getReplaceResource: function (planId, resType, resId) {
    var plan = this.getPlan(planId);
    if (!plan) {
      return {};
    }
    var replaceResources = plan.replace_resources;
    for (var index in replaceResources) {
      if (replaceResources[index].resource_type == resType && replaceResources[index].des_id == resId) {
        return replaceResources[index];
      }
    }
    return {};
  },
  getDependency: function (dependencies, resType, resId) {
    for (var index in dependencies) {
      if (dependencies[index].type == resType && dependencies[index].id == resId) {
        return dependencies[index];
      }
    }
    return {}
  },
  removeDependency: function (dependencies, resType, resId) {
    // var newDeps = [];
    for (var index in dependencies) {
      if (dependencies[index].type == resType && dependencies[index].id == resId) {
        dependencies.splice(index, 1);
        // newDeps.push(dependencies[index]);
      }
    }
    // console.log('newDeps')
    // console.log(newDeps)
    // dependencies = newDeps;
  },
  /*
  * Search the dependent resources. Mainly for showing resource editing modal view.
  * */
  searchDependentItems: function (dependencies, resType, resIds, searchedResType, except) {
    if (!except) {
      except = [];
    }
    var resId, dep, depRes, searchedResIds = [];
    for (var index in resIds) {
      resId = resIds[index];
      dep = this.getDependency(dependencies, resType, resId);
      if(!Object.keys(dep).length || dep.hasOwnProperty('searched')) {
        continue;
      }
      if (dep.type == searchedResType) {
        searchedResIds.push(dep.id)
      }
      dep['searched'] = true;
      for (var idx in dep.dependencies) {
        depRes = dep.dependencies[idx];
        Array.prototype.push.apply(searchedResIds, this.searchDependentItems(dependencies, depRes.type, [depRes.id], searchedResType, except));
      }
      var dep1;
      for (var depIdx in dependencies) {

        dep1 = dependencies[depIdx];
        if (dep1.hasOwnProperty('searched')) {
          continue;
        }
        for (idx in dep1.dependencies) {
          depRes = dep1.dependencies[idx];
          if (depRes.type == dep.type && depRes.id == dep.id) {
            Array.prototype.push.apply(searchedResIds, this.searchDependentItems(dependencies, dep1.type, [dep1.id], searchedResType, except));
          }
        }
      }
    }

    for (var expIdx in except) {
      var i = $.inArray(except[expIdx], searchedResIds);
      if (i > -1) {
        searchedResIds.slice(i, 1);
      }
    }

    return searchedResIds
  },
  checkDepIn: function (dep, dependencies) {
    for(var index in dependencies) {
      if(dep.id == dependencies[index].id && dep.type == dependencies[index].type) {
        return true;
      }
    }
    return false;
  },
  localDependencies: function (planId, resType, resId) {
    var plan = this.getPlan(planId);
    if (!plan) {
      return [];
    }
    var localDeps = [];
    var updatedDeps = plan.updated_deps;
    var coreDep = this.getDependency(updatedDeps, resType, resId);
    var dep;
    localDeps.push($.extend(true, {}, coreDep));
    for (var index in updatedDeps) {
      dep = updatedDeps[index];
      if(this.checkDepIn(dep, coreDep.dependencies) || this.checkDepIn(coreDep, dep.dependencies)) {
        localDeps.push($.extend(true, {}, dep));
      }
    }
    return localDeps;
  },
  globalDependencies: function (planId) {
    var plan = this.getPlan(planId);
    if (!plan) {
      return [];
    }
    var globalDeps = [];
    for (var index in plan.updated_deps) {
      globalDeps.push($.extend(true, {}, plan.updated_deps[index]))
    }
    return globalDeps;
  },
  extractResourceShowInfo: function (planId, resType, resId) {
    var updateRes = conveyorPlan.getUpdateResource(planId, resType, resId);
    var newRes = $.extend({}, updateRes, {"resource_type": resType, "resource_id": resId});

    var deps = [];
    var dependencies = this.getPlan(planId).updated_deps;
    for (var idx in dependencies) {
      deps.push($.extend({}, dependencies[idx]));
    }
    if ($.inArray(resType, ['OS::Neutron::Net', 'OS::Neutron::Subnet', 'OS::Neutron::SecurityGroup']) > -1) {
      var depServers = this.searchDependentItems(deps, resType, [resId], 'OS::Nova::Server');
      if (depServers.length) {
        newRes['HAS_SERVER'] = true;
      }
    }

    return newRes;
  },
  extractCloneInfo: function (planId, incrementalClone) {
    var plan = this.getPlan(planId);
    if (!plan) {
      return {};
    }
    var cloneResList = [];
    var cloneLinks = [];
    var updateResList = [];
    var replaceResList = [];
    var dep, link, updateRes;
    if (incrementalClone) {
      for (var index in plan.updated_deps) {
        dep = plan.updated_deps[index];
        if (!dep.is_cloned) {
          cloneResList.push({id: dep.id, type: dep.type})
        }
        for (var linkIdx in dep.dependencies) {
          link = dep.dependencies[linkIdx];
          if (!link.is_cloned && (dep.is_cloned || this.getDependency(plan.updated_deps, link.type, link.id).is_cloned)) {
            cloneLinks.push({src_id: link.id, attach_id: dep.id, src_type: link.type, attach_type: dep.type})
          }
        }
      }
    } else {
      for (var index in plan.updated_deps) {
        dep = plan.updated_deps[index];
        cloneResList.push({id: dep.id, type: dep.type})
      }
    }
    updateResList = plan.update_resources;
    replaceResList = plan.replace_resources;
    return {
      clone_resources: cloneResList,
      clone_links: cloneLinks,
      update_resources: updateResList,
      replace_resources: replaceResList
    }
  },
  /*
  * Get the dependent resources of some item. (mainly for update plan)
  * */
  getDependentResources: function (deps, resType, resId, depType, excepts) {
    var _depType;
    if (!depType) {
      _depType = this.dependentResMap[resType] || [];
    } else {
      _depType = depType;
    }
    if (_depType.length == 0) {
      return [];
    }

    if (!excepts) {
      excepts = [];
    }

    var thisRes = this.getDependency(deps, resType, resId);
    var depResList = [];
    var dep;
    for(var idx in deps) {
      dep = deps[idx];
      if($.inArray(dep.type, _depType) > -1
        && (this.checkDepIn(thisRes, dep.dependencies) || this.checkDepIn(dep, thisRes.dependencies))
        && $.inArray(dep.id, excepts) === -1) {
        depResList.push(dep);
      }
    }
    return depResList;
  },
  /*
  * Replace current resource with another existed resource.*/
  replaceResource: function (plan, resType, srcId, desId) {
    // var oriId = data.resource_id;
    // var newId = data.id;
    // var resType = data.resource_type;
    if (!resType || !srcId || !desId || srcId == desId) {
      return;
    }

    // Update replace_resources and update_resources
    // For replace_resources: if the specific item exists, then update desId, else add new replace resource item.
    var existed = false;
    var replaceResList = plan.replace_resources;
    for (var index in replaceResList) {
      var res = replaceResList[index];
      if(res.resource_type == resType && res.id == srcId) {
        // The original id could not be changed.
        res.id = desId;
        existed = true;
        break;
      }
    }
    if (!existed) {
      replaceResList.push({src_id: srcId, des_id: desId, resource_type: resType})
    }
    // For update_resources: if the specific item whose id and resource_type accorponse to srcId and resType, then remove it.
    var updateResList = plan.update_resources;
    for(var idx in updateResList) {
      if(updateResList[idx].resource_type == resType && updateResList[idx].resource_id == srcId) {
        updateResList.splice(idx, 1);
      }
    }
  },
  replaceResourceSelf: function (dependencies, resType, srcId, desId) {
    var dep = this.getDependency(dependencies, resType, desId);
    if (Object.keys(dep).length) {
      this.removeDependency(dependencies, resType, srcId);
    } else {
      dep = this.getDependency(dependencies, resType, srcId);
      dep.id = desId;
    }
  },
  changeCommonResource: function (plan, resType, srcId, desId) {
    this.replaceResource(plan, resType, srcId, desId);
    var dep, depRes;
    for (var idx in plan.updated_deps) {
      dep = plan.updated_deps[idx];
      for (var depIdx in dep.dependencies) {
        depRes = dep.dependencies[depIdx];
        if (depRes.type == resType && depRes.id == srcId) {
          depRes.id = desId;
        }
      }
    }
    this.replaceResourceSelf(plan.updated_deps, resType, srcId, desId)
  },
  changePortFromSubnet: function (plan, portRes, srcSubnetId, newSubnet) {
    var resType = 'OS::Neutron::Port';

    // Update port self
    var dep;
    for(var idx in portRes.dependencies) {
      dep = portRes.dependencies[idx];
      if (dep.type == 'OS::Neutron::Subnet' && dep.id == srcSubnetId) {
        dep.id = newSubnet.id;
      }
    }

    var portUpdateResource = this.getUpdateResource(plan.plan_id, resType, portRes.id);
    var fixedIps;
    if (portUpdateResource && portUpdateResource.fixed_ips) {
      fixedIps = portUpdateResource.fixed_ips;
    } else {
      fixedIps = conveyorService.getResource(resType, portRes.id).fixed_ips;
    }
    var fixedIp;
    for (var ipIdx in fixedIps) {
      fixedIp = fixedIps[ipIdx];
      if (fixedIp.subnet_id == srcSubnetId) {
        fixedIp.subnet_id = newSubnet.id;
        fixedIp.ip_address = '';
      }
    }
    this.updateUpdateResource(plan.plan_id, resType, portRes.id, {fixed_ips: fixedIps});
  },
  changePortFromNet: function (plan, portRes, srcNetId, desNetId) {
    // Here only change the port network dependency's id from srcNetId to desNetId
    var depRes;
    for(var idx in portRes.dependencies) {
      depRes = portRes.dependencies[idx];
      if (depRes.type == 'OS::Neutron::Net' && depRes.id == srcNetId) {
        depRes.id = desNetId;
      }
    }
  },
  changeSubnetFromNet: function (plan, subnetRes, srcNetId, desNetId) {
    var resType = 'OS::Neutron::Subnet';
    var subnets = conveyorService.getResources(resType, {'network_id': desNetId});
    if(!subnets) {
      return;
    }

    // Select one new subnet to replace current subnet.
    var newSubnet = null;
    if (subnets.length == 1) {
      newSubnet = subnets[0];
    } else {
      for (var subnetIdx in subnets) {
        if(!Object.keys(this.getDependency(plan.updated_deps, resType, subnets[subnetIdx].id)).length) {
          newSubnet = subnets[subnetIdx];
        }
      }
    }
    if (!newSubnet) {
      newSubnet = subnets[0];
    }
    var newSubnetId = newSubnet.id;

    // Update replace_resources
    this.replaceResource(plan, resType, subnetRes.id, newSubnet.id);

    // Update dependent items(OS::Neutron::Port).
    var depResList = this.getDependentResources(plan.updated_deps, resType, subnetRes.id);
    for(var idx in depResList) {
      this.changePortFromSubnet(plan, depResList[idx], subnetRes.id, newSubnet);
    }

    // Update subnet self
    var dep = this.getDependency(plan.updated_deps, resType, newSubnetId);
    if (Object.keys(dep).length) {
      this.removeDependency(plan.updated_deps, resType, subnetRes.id);
    } else {
      subnetRes.id = newSubnetId;
      var dep;
      for(idx in subnetRes.dependencies) {
        dep = subnetRes.dependencies[idx];
        if (dep.type == 'OS::Neutron::Net' && dep.id == srcNetId) {
          dep.id = desNetId;
        }
      }
    }
  },
  changeSubnet: function (plan, srcId, desId) {
    var resType = 'OS::Neutron::Subnet';
    // 1. Update replace_resources.
    this.replaceResource(plan, resType, srcId, desId);

    // 2. Update dependent items.
    var depResList = this.getDependentResources(plan.updated_deps, resType, srcId);
    for(var idx in depResList) {
      this.changePortFromSubnet(plan, depResList[idx], srcId, conveyorService.getResource(resType, desId));
    }

    // 3. Update subnet self.
    this.replaceResourceSelf(plan.updated_deps, resType, srcId, desId);
  },
  changeNet: function (plan, srcId, desId) {
    var resType = 'OS::Neutron::Net';
    // 1. Update replace_resources.
    this.replaceResource(plan, resType, srcId, desId);

    // 2. Update updated_deps
    // 2.1 Update dependent items
    var depResList = this.getDependentResources(plan.updated_deps, resType, srcId);
    var depRes;
    for (var idx in depResList) {
      depRes = depResList[idx];
      if (depRes.type == 'OS::Neutron::Subnet') {
        this.changeSubnetFromNet(plan, depRes, srcId, desId)
      } else if (depRes.type == 'OS::Neutron::Port') {
        this.changePortFromNet(plan, depRes, srcId, desId);
      }
    }

    // 3. Update network self
    this.replaceResourceSelf(plan.updated_deps, resType, srcId, desId);
  },
  /*
  * Update the one of resources of plan with some simple fields, or replace with another resource.*/
  updatePlanResource: function (planId, resType, resId, data) {
    if(data.needPosted) {
      var desId = data.data.id;
      var plan = this.getPlan(planId);
      if (!plan) {
        return;
      }

      if ($.inArray(resType, ['OS::Nova::KeyPair', 'OS::Cinder::VolumeType', 'OS::Neutron::SecurityGroup']) > -1) {
        this.changeCommonResource(plan, resType, resId, desId)
      }
      else if (resType == 'OS::Neutron::Net') {
        this.changeNet(plan, resId, desId)
      } else if (resType == 'OS::Neutron::Subnet') {
        this.changeSubnet(plan, resId, desId)
      }
    } else {
      this.updateUpdateResource(planId, resType, resId, data.data);
    }
  }
};
