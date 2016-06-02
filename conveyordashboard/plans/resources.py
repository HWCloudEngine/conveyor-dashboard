# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import base64
import json
import logging

from django.template import loader

from conveyordashboard.api import api
from conveyordashboard.api import models
from conveyordashboard.constant import (DEPENDENCY_UPDATE_MAPPING,
                                        TAG_RES_TYPE,
                                        TAG_RES_ID,
                                        TAG_FROM,
                                        TAG_FROM_ID,
                                        TAG_UPDATED)
from conveyordashboard.topology import tables as topology_tables

LOG = logging.getLogger(__name__)


def rebuild_dependencies(dependencies):
    """
    Add reverse dependencies to original dependencies.
    :param dependencies: original dependencies.
    """
    for res_id, item in dependencies.items():
        if not item.get("reverse_d", None):
            item["reverse_d"] = []
        if item["dependencies"]:
            for d in item["dependencies"]:
                if not dependencies[d].get("reverse_d", None):
                    dependencies[d]["reverse_d"] = [res_id]
                else:
                    dependencies[d]["reverse_d"].append(res_id)


def search_dependent_items(dependencies,
                           res_ids,
                           search_res_type,
                           excepts=None,
                           reverse=False):
    """
    search dependent item.
    :param dependencies:    dependencies used to search.
    :param res_ids:         list of resource id in heat template.
    :param search_res_type: destination resource type that needed to be search.
                            like: server
    :param excepts:         list of resource id. The search result should not
                            contain them.
    :param reverse:         True of False. This parameter depend search
                            direction. When reverse=True, the dependencies
                            must contains reversed dependencies.
    :return:                The list of id matched to search_res_type.
    """
    if not excepts:
        excepts = []

    searched_ids = []

    dep_pro = "dependencies" if not reverse else "reverse_d"
    for res_id in res_ids:
        for dep_res_id in dependencies[res_id][dep_pro]:
            if search_res_type == dep_res_id.split("_")[0]:
                searched_ids.append(dep_res_id)
            else:
                searched_ids.extend(search_dependent_items(dependencies,
                                                           [dep_res_id],
                                                           search_res_type,
                                                           excepts=excepts,
                                                           reverse=reverse))
    for e in excepts:
        if e in searched_ids:
            searched_ids.remove(e)

    return searched_ids


class ResourceDetailFromPlan(object):
    container = 'plans/res_detail/_balloon_container.html'

    def __init__(self, request,
                 plan_id,
                 res_type,
                 res_id,
                 update_data,
                 updated_res=None,
                 is_original=True):
        self.request = request
        self.plan_id = plan_id
        self.res_type = res_type
        self.res_id = res_id
        self.update_data = update_data
        if not updated_res:
            updated_res = {}
        self.updated_res=updated_res
        self.is_original = is_original
        self.type = self.res_type.split("::")[-1].lower()
        self.template_name = "%s%s%s" % ('plans/res_detail/',
                                         self.type,
                                         '.html')            

    def _render_server(self, context):
        resource_detail = context["data"]
        if not self.update_data.has_key("user_data"):
            if resource_detail.get('user_data', None):
                resource_detail["user_data"] = \
                    base64.b64decode(resource_detail["user_data"]
                                    .encode('utf-8'))
        metadata = resource_detail.get('metadata', {})
        metadata = [models.Metadata({"key": key, "value": value})
                    for key, value in metadata.items()]
        LOG.info("Metadata={}".format(metadata))
        md_table = topology_tables.MetadataTable(self.request, metadata)
        context["metadata"] = md_table.render()
        return loader.render_to_string(self.container, context)

    def _render_keypair(self, context):
        resource_detail = context["data"]
        keypairs = api.resource_list(self.request, "OS::Nova::KeyPair")
        resource_detail["keypairs"] = keypairs
        return loader.render_to_string(self.container, context)

    def _render_net(self, context):
        resource_detail = context["data"]
        is_external = resource_detail.get("value_specs", {})\
                                     .get("router:external", False)
        tenant_id = self.request.user.tenant_id
        networks = api.net_list_for_tenant(self.request, tenant_id)
        networks = [network for network in networks 
                    if (getattr(network, "router:external") == is_external
                        and len(network.subnets) > 0)]
        
        #remove conflict network
        plan = api.plan_get(self.request, self.plan_id)
        dependencies = plan.updated_dependencies
        updated_res = dict(plan.updated_resources, **self.updated_res)
        rebuild_dependencies(dependencies)
        dep_servers = search_dependent_items(dependencies,
                                             [self.res_id],
                                             "server",
                                             reverse=True)
        dep_networks = search_dependent_items(dependencies,
                                              dep_servers,
                                              "network",
                                              excepts=[self.res_id])

        networks = dict([(n.id, n) for n in networks])
        for dep_network in dep_networks:
            if updated_res[dep_network]["id"] in networks:
                del networks[updated_res[dep_network]["id"]]

        context["data"]['networks'] = networks.values()
        return loader.render_to_string(self.container, context)

    def _render_subnet(self, context):
        tenant_id = self.request.user.tenant_id
        subnets = api.subnet_list_for_tenant(self.request, tenant_id)

        resource_detail = context["data"]
        if resource_detail.has_key("from_network_id"):
            subnets = [subnet for subnet in subnets
                       if subnet.network_id ==
                          resource_detail.get("from_network_id")]
        
        #remove conflict subnet.
        plan = api.plan_get(self.request, self.plan_id)
        dependencies = plan.updated_dependencies
        updated_res = dict(plan.updated_resources, **self.updated_res)
        rebuild_dependencies(dependencies)
        dep_servers = search_dependent_items(dependencies,
                                             [self.res_id],
                                             "server",
                                             reverse=True)
        dep_subnets = search_dependent_items(dependencies,
                                             dep_servers,
                                             "subnet",
                                             excepts=[self.res_id])

        subnets = dict([(s.id, s) for s in subnets])
        for dep_subnet in dep_subnets:
            if updated_res[dep_subnet]["id"] in subnets:
                del subnets[updated_res[dep_subnet]["id"]]

        resource_detail["subnets"] = subnets.values()
        return loader.render_to_string(self.container, context)

    def _render_port(self, context):
        plan = api.plan_get(self.request, self.plan_id)
        fixed_ips = context["data"]["fixed_ips"]
        
        #Get detail subnet information for each fixed ip in fixed_ips.
        #And Unite the format for fixed_ips.
        for fixed_ip in fixed_ips:
            fip_subnet_id = fixed_ip["subnet_id"]
            if isinstance(fip_subnet_id, str):
                subnet_id = fip_subnet_id
                for key, res in self.updated_res.items():
                    if res["id"] == subnet_id:
                        fixed_ip["subnet_id"] = {"get_resource": key}
                if not isinstance(fixed_ip["subnet_id"], dict):
                    for key, res in plan.updated_dependencies.items():
                        if res["id"] == subnet_id:
                            fixed_ip["subnet_id"] = {"get_resource": key}
            elif isinstance(fip_subnet_id, dict):
                if fip_subnet_id.get("get_resource", None):
                    res_id_subnet = fip_subnet_id["get_resource"]
                elif fip_subnet_id.get("get_param", None):
                    subnet_id = self.res.get("parameters", {}).get(fip_subnet_id["get_param"], None)
                    if not subnet_id:
                        raise Exception
                    for key, res in self.updated_res.items():
                        if res["id"] == subnet_id:
                            fixed_ip["subnet_id"] = {"get_resource": key}
                    if "get_resource" not in fixed_ip["subnet_id"]:
                        for key, res in plan.updated_dependencies.items():
                            if res["id"] == subnet_id:
                                fixed_ip["subnet_id"] = {"get_resource": key}
                else:
                    raise Exception

                if self.updated_res.has_key(res_id_subnet):
                    subnet_id = self.updated_res[res_id_subnet]["id"]
                else:
                    subnet_id = plan.updated_dependencies[res_id_subnet]["id"]
            else:
                raise Exception               
#             res_id_subnet = fixed_ip["subnet_id"]["get_resource"]
# 
#             if self.updated_res.has_key(res_id_subnet):
#                 subnet_id = self.updated_res[res_id_subnet]["id"]
#             else:
#                 subnet_id = dependencies[res_id_subnet]["id"]
            subnet = api.resource_detail(self.request,
                                         "OS::Neutron::Subnet",
                                         subnet_id)
            fixed_ip["cidr"] = subnet["cidr"]
            fixed_ip["allocation_pools"] \
                    = json.dumps(subnet["allocation_pools"])
        return loader.render_to_string(self.container, context)

    def _render_securitygroup(self, context):
        tenant_id = self.request.user.tenant_id
        secgroups = api.sg_list(self.request, tenant_id)
        context["data"]["secgroups"] = secgroups

        sg_id = context["id"]
        sg = None
        for item in secgroups:
            if item.id == sg_id:
                sg = item
                break

        if sg:
            rules_table = topology_tables.RulesTable(self.request, sg.rules)
            context["rules_table"] = rules_table.render()

        return loader.render_to_string(self.container, context)

    def _render_router(self, context):
        routers = api.resource_list(self.request, self.res_type)
        context["data"]["routers"] = routers
        return loader.render_to_string(self.container, context)

    def _render_floatingip(self, context):
        plan = api.plan_get(self.request, self.plan_id)
        fip_id = plan.original_resources[self.res_id]["id"]
        fips = api.resource_list(self.request, self.res_type)
        fips = [fip for fip in fips
                if fip.status == "DOWN" or fip.id == fip_id]
        context["data"]["fips"] = fips
        return loader.render_to_string(self.container, context)

    def render(self):
        if self.update_data.has_key("id"):
            resource = self.updated_res[self.res_id]
        else:
            #If the plan does not contains this resource, it will throw an
            #exception, then need to extract resource from api resource_get.
            resource = api.resource_detail_from_plan(self.request,
                                                     self.res_id,
                                                     self.plan_id,
                                                     self.is_original)
        self.res = resource
        resource_detail = resource["properties"]
        resource_detail.update(self.update_data)
        method = "_render_" + self.type
        context = {'type': type,
                   'template_name':self.template_name,
                   "resource_type": self.res_type,
                   "resource_id": self.res_id,
                   "id": resource.get("id", None),
                   'data': resource_detail}
        LOG.info("Render %s" % self.type)
        if hasattr(self, method):
            return getattr(self, method)(context)
        else:
            return loader.render_to_string(self.container, context)


class PlanUpdate(object):
    def __init__(self, request, plan_id, updated_resources, dependencies,
                 update_resource=None):
        """
        :param request:
        :param plan_id:
        :param updated_resources:   {} the full detail of resources that
                                    have been updated.
        :param dependencies:        [] the dependencies that have been updated.
        :param update_resource:     [] the collection of updated items of this
                                    resource.
        """
        self.request = request
        self.plan_id = plan_id
        self.updated_resources = updated_resources
        self.dependencies = dependencies
        if not update_resource:
            update_resource = {}
        self.update_resource = update_resource

    def _check_updated(self):
        if self.updated_resources[self.res_id].get("RES_UPDATED", False):
            return True
        return False

    def _dependent_items(self, excepts=[]):
        LOG.info("Get dependent items.\nresource_type={0}\nresource_id={1}\n"
                 "excepts={2}\nresources_dependencies={3}"
                 .format(self.res_type,
                         self.res_id,
                         excepts,
                         self.dependencies))

        dependent_items = {}
        dependent_type = DEPENDENCY_UPDATE_MAPPING.get(self.res_type, [])
        this_res = self.dependencies[self.res_id]

        for key, value in self.dependencies.items():
            if value["type"] in dependent_type \
                and (self.res_id in value["dependencies"]
                     or key in this_res["dependencies"])\
                and key not in excepts:
                dependent_items[key] = value
        LOG.info("Get dependent items.\ndependent_items={0}"
                 .format(dependent_items))
        return dependent_items

    def execute(self, data):
        self.res_type = data.pop(TAG_RES_TYPE)
        self.res_id = data.pop(TAG_RES_ID)
        self.data = data
        method = "_update_" + self.res_type.split("::")[-1].lower()
        if hasattr(self, method):
            getattr(self, method)()

    def execute_return(self):
        return self.updated_resources, self.dependencies, self.update_resource

    def update_updated_resources(self, param):
        self.updated_resources[self.res_id].update(param)

    def update_dependencies(self, param):
        self.dependencies[self.res_id].update(param)

    def update_update_resource(self, param):
        param[TAG_RES_TYPE] = self.res_type
        param[TAG_RES_ID] = self.res_id
        self.update_resource.update({self.res_id: param})

    def _update_keypair(self):
        LOG.info("Update keypair")
        data = self.data
        res_id = self.res_id
        res_type = self.res_type
        this_res = self.updated_resources[res_id]
        keypair_name = self.data.get("name", None)
        if not keypair_name:
            return

        action_type = data.get("action_type", "update")
        keypairs = api.resource_list(self.request, res_type)
        if action_type == "update":
            keypair_name = data.get("name", None)
            if not keypair_name:
                return

            keypair = None
            for item in keypairs:
                if item.name == keypair_name:
                    keypair = item
                    break
            if not keypair:
                return

            new_id = keypair_name
            this_res.update({
                "id": new_id,
                TAG_UPDATED: True,
                "properties": {
                    "public_key": keypair.public_key,
                    "name": keypair_name}})
            self.dependencies.get(res_id).update({"id": new_id,
                                                       "name": keypair_name})
            self.update_resource.update({
                res_id: {"type": res_type,
                         "res_id": res_id,
                         "name": keypair_name,
                         "public_key": keypair.public_key,
                         "id": new_id}})

    def _update_port(self):
        LOG.info("Update port")
        data = self.data
        res_id = self.res_id
        res_type = self.res_type
        this_res = self.updated_resources[res_id]

        update_from = data.get(TAG_FROM, None)
        if update_from:
            if update_from == "subnet":
                from_id = data[TAG_FROM_ID]
                fixed_ips = this_res["properties"]["fixed_ips"]
                for fixed_ip in fixed_ips:
                    #
                    subnet_id = fixed_ip["subnet_id"]
                    if isinstance(subnet_id, str):
                        if subnet_id == self.updated_resources[from_id]["id"]:
                            fixed_ip["ip_address"] = ""
                    elif isinstance(subnet_id, dict):
                        if subnet_id.get("get_resource", None):
                            if subnet_id["get_resource"] == from_id:
                                fixed_ip["ip_address"] = ""
                        elif subnet_id.get("get_param", None):
                            p_sn_id = this_res.get("parameters", {}).get(subnet_id["get_param"], {}).get("default", None)
                            if not p_sn_id:
                                raise Exception
                            if p_sn_id == self.updated_resources[from_id]["id"]:
                                fixed_ip["ip_address"] = ""
                            
                    #
#                     if fixed_ip["subnet_id"]["get_resource"] == from_id:
#                         fixed_ip["ip_address"] = ""
                this_res["properties"]["fixed_ips"] = fixed_ips
                this_res[TAG_UPDATED] = True
                self.update_resource.update({
                    res_id: dict({"type": res_type,
                                  "res_id": res_id,},
                                 **(this_res["properties"]))})
        else:
            pass

    def _update_subnet(self):
        LOG.info("Update subnet")
        data = self.data
        res_id = self.res_id
        res_type = self.res_type
        this_res = self.updated_resources[res_id]
        if this_res.get(TAG_UPDATED, False):
            return

        update_from = data.get(TAG_FROM, None)
        if update_from:
            if update_from == "net":
                from_id = data[TAG_FROM_ID]
                network_id = data["network_id"]
                subnet_id = api.resource_detail(self.request,
                                                "OS::Neutron::Net",
                                                network_id)["subnets"][0]
                subnet = api.resource_detail(self.request,
                                             res_type,
                                             subnet_id)
                update_data = {
                    "id": subnet["id"],
                    "properties":{
                        "name": subnet["name"],
                        "enable_dhcp": subnet["enable_dhcp"],
                        "allocation_pools": subnet["allocation_pools"],
                        "gateway_ip": subnet["gateway_ip"],
                        "ip_version": subnet["ip_version"],
                        "cidr": subnet["cidr"]
                    },
                    TAG_UPDATED: True
                }
                this_res.update(update_data)
                self.dependencies.get(res_id).update({"id": subnet["id"],
                                                      "name": subnet["name"]})
                self.update_resource.update({
                    res_id: dict({"type": res_type,
                                  "res_id": res_id,
                                  "id":subnet["id"],
                                  "name": subnet["name"],},
                                 **(update_data["properties"]))})
                dependent_items = self._dependent_items(excepts=[from_id])
                for key, value in dependent_items.items():
                    data = {TAG_RES_TYPE: value["type"],
                            TAG_RES_ID: key,
                            TAG_FROM: "subnet",
                            TAG_FROM_ID: res_id}
                    if value["type"] == "OS::Neutron::Net":
                        data["subnet_id"] = subnet["id"]
                    elif value["type"] == "OS::Neutron::Port":
                        data["subnet_id"] = subnet["id"]
                    self.execute(data)
        else:
            new_subnet_id = data.get("id", None)
            subnet = api.resource_detail(self.request,
                                         res_type,
                                         new_subnet_id)
            update_data = {
                "id": new_subnet_id,
                "properties": {
                    "name": subnet["name"],
                    "enable_dhcp": subnet["enable_dhcp"],
                    "allocation_pools": subnet["allocation_pools"],
                    "gateway_ip": subnet["gateway_ip"],
                    "ip_version": subnet["ip_version"],
                    "cidr": subnet["cidr"]
                },
                TAG_UPDATED: True
            }
            this_res.update(update_data)
            self.dependencies.get(res_id).update({"id": new_subnet_id,
                                                  "name": subnet["name"]})
            self.update_resource.update({
                                res_id: dict({"type": res_type,
                                              "res_id": res_id,
                                              "id":new_subnet_id,
                                              "name": subnet["name"],},
                                             **(update_data["properties"]))})
            dependent_items = self._dependent_items()
            for key, value in dependent_items.items():
                data = {TAG_RES_TYPE: value["type"],
                        TAG_RES_ID: key,
                        TAG_FROM_ID:res_id,
                        TAG_FROM: "subnet"}
                if value["type"] == "OS::Neutron::Net":
                    data["subnet_id"] = new_subnet_id
                    if subnet["network_id"] == value["id"]:
                        continue
                elif value["type"] == "OS::Neutron::Port":
                    data["subnet_id"] = new_subnet_id
                self.execute(data)

    def _modify_subnet_src(self, res_id, network_id):
        subnet_items = []
        for key, value in self.dependencies.items():
            if (res_id in value["dependencies"]
                and value[TAG_RES_TYPE] == "OS::Neutron::Subnet"):
                subnet_items.append(key)
        for item in subnet_items:
            self.updated_resources[item]["from_network_id"] = network_id
            self.update_resource[item]["from_network_id"] = network_id

    def _update_net(self):
        LOG.info("Update network")
        data = self.data
        res_id = self.res_id
        res_type = self.res_type
        this_res = self.updated_resources[res_id]
        if this_res.get(TAG_UPDATED, False):
            return

        update_from = data.get(TAG_FROM, None)
        if update_from:
            from_id = data[TAG_FROM_ID]
            if update_from == "subnet":
                subnet_id = data["subnet_id"]
                subnet = api.resource_detail(self.request,
                                             "OS::Neutron::Subnet",
                                             subnet_id)
                network_id = subnet["network_id"]
                network = api.resource_detail(self.request,
                                              res_type,
                                              network_id)
                update_data = {
                    "properties": {
                        "shared": network["shared"],
                        "admin_state_up": network["admin_state_up"],
                        "value_specs": {
                            "router:external": network["router:external"],
                            "provider:network_type":
                                    network["provider:network_type"],
                            "provider:physical_network":
                                    network["provider:physical_network"],
                            "provider:segmentation_id":
                                    network["provider:segmentation_id"]
                        },
                        "name": network["name"]
                    },
                    "id": network_id,
                    TAG_UPDATED: True
                }
                this_res.update(update_data)
                self.dependencies.get(res_id).update({
                                                "id": network["id"],
                                                "name": network["name"]})
                self.update_resource.update({
                        res_id: dict({"type": res_type,
                                      "res_id": res_id,
                                      "id":network_id,
                                      "name": network["name"],},
                                     **(update_data["properties"]))})
                dependent_items = self._dependent_items(excepts=[from_id])
                for key, value in dependent_items.items():
                    data = {TAG_RES_TYPE: value["type"],
                            TAG_RES_ID: key,
                            TAG_FROM: "net",
                            TAG_FROM_ID: res_id}
                    if value["type"] == "OS::Neutron::Subnet":
                        data["network_id"] = network_id
                    self.execute(data)
                self._modify_subnet_src(res_id, network_id)
        else:
            network_id = data["id"]
            network = api.net_get(self.request, network_id)

            update_data = {
                "properties": {
                    "shared": network["shared"],
                    "admin_state_up": network["admin_state_up"],
                    "value_specs": {
                        "router:external": network["router:external"],
                        "provider:network_type":
                            network["provider:network_type"],
                        "provider:physical_network":
                            network["provider:physical_network"],
                        "provider:segmentation_id":
                            network["provider:segmentation_id"]},
                    "name": network["name"]
                    },
                "id": network_id,
                TAG_UPDATED: True
            }

            this_res.update(update_data)
            self.dependencies.get(res_id).update({"id": network_id,
                                              "name": network["name"]})
            self.update_resource.update({res_id:
                                         dict({"type": res_type,
                                               "res_id": res_id,
                                               "id":network_id,
                                               "name": network["name"],},
                                              **(update_data["properties"]))})

            dependent_items = self._dependent_items()
            for key, value in dependent_items.items():
                data = {TAG_RES_TYPE: value["type"],
                        TAG_RES_ID: key,
                        TAG_FROM: "net",
                        TAG_FROM_ID: res_id}
                if value["type"] == "OS::Neutron::Subnet":
                    data["network_id"] = network_id
                self.execute(data)

            self._modify_subnet_src(res_id, network_id)

    def _update_securitygroup(self):
        LOG.info("Update security group")
        data = self.data
        res_id = self.res_id
        res_type = self.res_type
        this_res = self.updated_resources[res_id]
        
        def _build_rules(rules):
            brules = []
            dependencies = []
            for rule in rules:
                if rule.get('protocol') == 'any':
                    del rule['protocol']
                #Only extract secgroups in first level,
                #ignore the dependent secgroup.
                rg_id = rule.get('remote_group_id')
                if rg_id is not None:
                    rule['remote_mode'] = "remote_group_id"
                    if rg_id == rule.get('security_group_id'):
                        del rule['remote_group_id']
                            
                del rule['tenant_id']
                del rule['id']
                del rule['security_group_id']
                rule = dict((k, v) for k, v in rule.items() if v is not None)
                brules.append(rule)
            return brules, dependencies

        if this_res.get(TAG_UPDATED, False):
            return

        update_from = data.get(TAG_FROM, None)
        if update_from:
            pass
        else:
            sg_id = data.pop("id", None)

            #If security group id changed, then update this_res.
            if sg_id:
                new_sg = api.sg_get(self.request, sg_id)
                rules = _build_rules(new_sg.security_group_rules)[0]

                update_data = {
                    "id": sg_id,
                    TAG_UPDATED: True,
                    "properties": {"name": new_sg.name,
                                   "description": new_sg.description,
                                   "rules": rules}
                }
                this_res.update(update_data)
                self.dependencies.get(res_id).update({"id": sg_id,
                                                      "name": new_sg.name})
                update_data = {res_id: dict({"type": res_type,
                                             "res_id": res_id,
                                             "id": sg_id},
                                            **(this_res["properties"]))}
                self.update_resource.update(update_data)

            #Is there some rule items need to be delete.
            del_rule_ids = data.pop("del_rule_ids", None)
            if del_rule_ids:
                del_rule_ids = del_rule_ids.split(" ")
                pass

    def _update_floatingip(self):
        LOG.info("Update floating ip")
        data = self.data
        res_id = self.res_id
        res_type = self.res_type
        this_res = self.updated_resources[res_id]
        if this_res.get(TAG_UPDATED, False):
            return

        update_from = data.get(TAG_FROM, None)
        if update_from:
            pass
        else:
            fip_id = data["id"]
            update_data = {"id": fip_id,
                           TAG_UPDATED: True}
            this_res.update(update_data)
            self.dependencies.get(res_id).update({"id": fip_id})
            update_data = {res_id: dict({"type": res_type,
                                         "res_id": res_id,
                                         "id": fip_id},
                                        **(this_res["properties"]))}
            self.update_resource.update(update_data)


def update_return_resource(res_src, res_update_data, dep_src, dep_update_data):
    for key, value in res_update_data.items():
            if value.has_key(TAG_UPDATED):
                del value[TAG_UPDATED]
                res_src.update({key: value})

    dep_src = dict([(key, dep_update_data[key]) for key in res_src.keys()])
    return res_src, dep_src
