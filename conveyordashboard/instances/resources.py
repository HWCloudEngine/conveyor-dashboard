import base64
import json
import logging

from django.template import loader

from openstack_dashboard import api as openstack_api

from conveyordashboard.api import api
from conveyordashboard.constant import (DEPENDENCY_UPDATE_MAPPING,
                                      TAG_RES_TYPE,
                                      TAG_RES_ID,
                                      TAG_FROM,
                                      TAG_FROM_ID,
                                      TAG_UPDATED)
from conveyordashboard.instances import tables as inst_tables

LOG = logging.getLogger(__name__)


class ResourceDetailFromPlan(object):
    container = 'instances/client_side/_balloon_container.html'

    def __init__(self, request,
                 plan_id,
                 resource_type,
                 resource_id,
                 update_data,
                 updated_res=None,
                 is_original=True):
        self.request = request
        self.plan_id = plan_id
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.update_data = update_data
        if not updated_res:
            updated_res = {}
        self.updated_res=updated_res
        self.is_original = is_original
        self.type = self.resource_type.split("::")[-1].lower()
        self.template_name = "%s%s%s" % ('instances/client_side/',
                                         self.type,
                                         '.html')

    def _render_server(self, context):
        if not self.update_data.has_key("user_data"):
            resource_detail = context["data"]
            if resource_detail.get('user_data', None):
                resource_detail["user_data"] = \
                    base64.b64decode(resource_detail["user_data"]
                                    .encode('utf-8'))
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
        context["data"]['networks'] = networks
        return loader.render_to_string(self.container, context)

    def _render_subnet(self, context):
        tenant_id = self.request.user.tenant_id
        subnets = api.subnet_list_for_tenant(self.request, tenant_id)

        resource_detail = context["data"]
        if resource_detail.has_key("from_network_id"):
            subnets = [subnet for subnet in subnets
                       if subnet.network_id ==
                          resource_detail.get("from_network_id")]
        resource_detail["subnets"] = subnets
        return loader.render_to_string(self.container, context)

    def _render_port(self, context):
        plan = api.plan_get(self.request, self.plan_id)
        dependencies = plan.original_dependencies
        fixed_ips = context["data"]["fixed_ips"]
        for fixed_ip in fixed_ips:
            res_id_subnet = fixed_ip["subnet_id"]["get_resource"]

            if self.updated_res.has_key(res_id_subnet):
                subnet_id = self.updated_res[res_id_subnet]["id"]
            else:
                subnet_id = dependencies[res_id_subnet]["id"]
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
            sg_table = inst_tables.RulesTable(self.request, sg.rules)
            context["sg_table"] = sg_table.render()

        return loader.render_to_string(self.container, context)

    def _render_router(self, context):
        routers = api.resource_list(self.request, self.resource_type)
        context["data"]["routers"] = routers
        return loader.render_to_string(self.container, context)

    def _render_floatingip(self, context):
        plan = api.plan_get(self.request, self.plan_id)
        fip_id = plan.original_resources[self.resource_id]["id"]
        fips = api.resource_list(self.request, self.resource_type)
        fips = [fip for fip in fips
                if fip.status == "DOWN" or fip.id == fip_id]
        context["data"]["fips"] = fips
        return loader.render_to_string(self.container, context)

    def render(self):
        resource = api.resource_detail_from_plan(self.request,
                                                 self.resource_id,
                                                 self.plan_id,
                                                 self.is_original)
        if self.update_data.has_key("id"):
            resource["id"] = self.update_data["id"]
        resource_detail = resource["properties"]
        resource_detail.update(self.update_data)
        method = "_render_" + self.type
        context = {'type': type,
                   'template_name':self.template_name,
                   "resource_type": self.resource_type,
                   "resource_id": self.resource_id,
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
        self.request = request
        self.plan_id = plan_id
        self.updated_resources = updated_resources
        self.dependencies = dependencies
        if not update_resource:
            update_resource = {}
        self.update_resource = update_resource

    def _check_updated(self):
        if self.updated_resources[self.resource_id].get("RES_UPDATED", False):
            return True
        return False

    def _dependent_items(self, excepts=[]):
        LOG.info("Get dependent items.\nresource_type={0}\nresource_id={1}\n"
                 "excepts={2}\nresources_dependencies={3}"
                 .format(self.resource_type,
                         self.resource_id,
                         excepts,
                         self.dependencies))

        dependent_items = {}
        dependent_type = DEPENDENCY_UPDATE_MAPPING.get(self.resource_type, [])
        this_resource = self.dependencies[self.resource_id]

        for key, value in self.dependencies.items():
            if value["type"] in dependent_type \
                and (self.resource_id in value["dependencies"]
                     or key in this_resource["dependencies"])\
                and key not in excepts:
                dependent_items[key] = value
        LOG.info("Get dependent items.\ndependent_items={0}"
                 .format(dependent_items))
        return dependent_items

    def execute(self, data):
        self.data = data
        self.resource_type = data.get(TAG_RES_TYPE)
        self.resource_id = data.get(TAG_RES_ID)
        method = "_update_" + self.resource_type.split("::")[-1].lower()
        if hasattr(self, method):
            getattr(self, method)()

    def execute_return(self):
        return self.updated_resources, self.dependencies, self.update_resource

    def update_updated_resources(self, param):
        self.updated_resources[self.resource_id].update(param)

    def update_dependencies(self, param):
        self.dependencies[self.resource_id].update(param)

    def update_update_resource(self, param):
        param[TAG_RES_TYPE] = self.resource_type
        param[TAG_RES_ID] = self.resource_id
        self.update_resource.update({self.resource_id: param})

    def _update_keypair(self):
        LOG.info("Update keypair")
        data = self.data
        resource_id = self.data[TAG_RES_ID]
        resource_type = self.data[TAG_RES_TYPE]
        this_resource = self.updated_resources[resource_id]
        keypair_name = self.data.get("name", None)
        if not keypair_name:
            return

        action_type = data.get("action_type", "update")
        keypairs = api.resource_list(self.request, resource_type)
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
            this_resource.update({
                "id": new_id,
                TAG_UPDATED: True,
                "properties": {
                    "public_key": keypair.public_key,
                    "name": keypair_name}})
            self.dependencies.get(resource_id).update({"id": new_id,
                                                       "name": keypair_name})
            self.update_resource.update({
                resource_id: {
                    "type": resource_type,
                    "res_id": resource_id,
                    "name": keypair_name,
                    "public_key": keypair.public_key,
                    "id": new_id}})

    def _update_port(self):
        LOG.info("Update port")
        data = self.data
        resource_id = data[TAG_RES_ID]
        resource_type = data[TAG_RES_TYPE]
        this_resource = self.updated_resources[resource_id]

        update_from = data.get(TAG_FROM, None)
        if update_from:
            if update_from == "subnet":
                from_id = data[TAG_FROM_ID]
                fixed_ips = this_resource["properties"]["fixed_ips"]
                for fixed_ip in fixed_ips:
                    if fixed_ip["subnet_id"]["get_resource"] == from_id:
                        fixed_ip["ip_address"] = ""
                this_resource["properties"]["fixed_ips"] = fixed_ips
                this_resource[TAG_UPDATED] = True
                self.update_resource.update({
                    resource_id: dict({"type": resource_type,
                                       "res_id": resource_id,},
                                      **(this_resource["properties"]))})
        else:
            pass

    def _update_subnet(self):
        LOG.info("Update subnet")
        data = self.data
        resource_id = data[TAG_RES_ID]
        resource_type = data[TAG_RES_TYPE]
        this_resource = self.updated_resources[resource_id]
        if this_resource.get(TAG_UPDATED, False):
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
                                             resource_type,
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
                this_resource.update(update_data)
                self.dependencies.get(resource_id).update({
                                                "id": subnet["id"],
                                                "name": subnet["name"]})
                self.update_resource.update({
                    resource_id: dict({"type": resource_type,
                                       "res_id": resource_id,
                                       "id":subnet["id"],
                                       "name": subnet["name"],},
                                      **(update_data["properties"]))})
                dependent_items = self._dependent_items(excepts=[from_id])
                for key, value in dependent_items.items():
                    data = {TAG_RES_TYPE: value["type"],
                            TAG_RES_ID: key,
                            TAG_FROM: "subnet",
                            TAG_FROM_ID: resource_id}
                    if value["type"] == "OS::Neutron::Net":
                        data["subnet_id"] = subnet["id"]
                    elif value["type"] == "OS::Neutron::Port":
                        data["subnet_id"] = subnet["id"]
                    self.execute(data)
        else:
            new_subnet_id = data.get("id", None)
            subnet = api.resource_detail(self.request,
                                         resource_type,
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
            this_resource.update(update_data)
            self.dependencies.get(resource_id).update({"id": new_subnet_id,
                                                       "name": subnet["name"]})
            self.update_resource.update({
                        resource_id: dict({"type": resource_type,
                                           "res_id": resource_id,
                                           "id":new_subnet_id,
                                           "name": subnet["name"],},
                                          **(update_data["properties"]))})
            dependent_items = self._dependent_items()
            for key, value in dependent_items.items():
                data = {TAG_RES_TYPE: value["type"],
                        TAG_RES_ID: key,
                        TAG_FROM_ID:resource_id,
                        TAG_FROM: "subnet"}
                if value["type"] == "OS::Neutron::Net":
                    data["subnet_id"] = new_subnet_id
                    if subnet["network_id"] == value["id"]:
                        continue
                elif value["type"] == "OS::Neutron::Port":
                    data["subnet_id"] = new_subnet_id
                self.execute(data)

    def _modify_subnet_src(self, resource_id, network_id):
        subnet_items = []
        for key, value in self.dependencies.items():
            if (resource_id in value["dependencies"]
                and value[TAG_RES_TYPE] == "OS::Neutron::Subnet"):
                subnet_items.append(key)
        for item in subnet_items:
            self.updated_resources[item]["from_network_id"] = network_id
            self.update_resource[item]["from_network_id"] = network_id

    def _update_net(self):
        LOG.info("Update network")
        data = self.data
        resource_id = data[TAG_RES_ID]
        resource_type = data[TAG_RES_TYPE]
        this_resource = self.updated_resources[resource_id]
        if this_resource.get(TAG_UPDATED, False):
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
                                              resource_type,
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
                this_resource.update(update_data)
                self.dependencies.get(resource_id).update({
                                                "id": network["id"],
                                                "name": network["name"]})
                self.update_resource.update({
                        resource_id: dict({"type": resource_type,
                                           "res_id": resource_id,
                                           "id":network_id,
                                           "name": network["name"],},
                                          **(update_data["properties"]))})
                dependent_items = self._dependent_items(excepts=[from_id])
                for key, value in dependent_items.items():
                    data = {TAG_RES_TYPE: value["type"],
                            TAG_RES_ID: key,
                            TAG_FROM: "net",
                            TAG_FROM_ID: resource_id}
                    if value["type"] == "OS::Neutron::Subnet":
                        data["network_id"] = network_id
                    self.execute(data)
                self._modify_subnet_src(resource_id, network_id)
        else:
            network_id = data["id"]
            network = openstack_api.neutron.network_get(self.request,
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
                            network["provider:segmentation_id"]},
                    "name": network["name"]
                    },
                "id": network_id,
                TAG_UPDATED: True
            }

            this_resource.update(update_data)
            self.dependencies.get(resource_id).update({"id": network_id,
                                              "name": network["name"]})
            self.update_resource.update({resource_id:
                                         dict({"type": resource_type,
                                               "res_id": resource_id,
                                               "id":network_id,
                                               "name": network["name"],},
                                              **(update_data["properties"]))})

            dependent_items = self._dependent_items()
            for key, value in dependent_items.items():
                data = {TAG_RES_TYPE: value["type"],
                        TAG_RES_ID: key,
                        TAG_FROM: "net",
                        TAG_FROM_ID: resource_id}
                if value["type"] == "OS::Neutron::Subnet":
                    data["network_id"] = network_id
                self.execute(data)

            self._modify_subnet_src(resource_id, network_id)

    def _update_securitygroup(self):
        LOG.info("Update security group")
        data = self.data
        resource_id = data[TAG_RES_ID]
        resource_type = data[TAG_RES_TYPE]
        this_resource = self.updated_resources[resource_id]
        if this_resource.get(TAG_UPDATED, False):
            return

        update_from = data.get(TAG_FROM, None)
        if update_from:
            pass
        else:
            sg_id = data["id"]
            new_sg = api.sg_get(self.request, sg_id)
            rules = [rule.__dict__ for rule in new_sg.rules]
            update_data = {"id": sg_id,
                       TAG_UPDATED: True,
                       "properties": {"name": new_sg.name,
                                      "description": new_sg.description,
                                      "rules": new_sg.security_group_rules}}
            this_resource.update(update_data)
            self.dependencies.get(resource_id).update({"id": sg_id,
                                                       "name": new_sg.name})
            update_data = {resource_id: dict({"type": resource_type,
                                              "res_id": resource_id,
                                              "id": sg_id},
                                             **(update_data["properties"]))}
            self.update_resource.update(update_data)

    def _update_floatingip(self):
        LOG.info("Update floating ip")
        data = self.data
        resource_id = data[TAG_RES_ID]
        resource_type = data[TAG_RES_TYPE]
        this_resource = self.updated_resources[resource_id]
        if this_resource.get(TAG_UPDATED, False):
            return

        update_from = data.get(TAG_FROM, None)
        if update_from:
            pass
        else:
            fip_id = data["id"]
            update_data = {"id": fip_id,
                           TAG_UPDATED: True}
            this_resource.update(update_data)
            self.dependencies.get(resource_id).update({"id": fip_id})
            update_data = {resource_id: dict({"type": resource_type,
                                              "res_id": resource_id,
                                              "id": fip_id},
                                             **(this_resource["properties"]))}
            self.update_resource.update(update_data)


def update_return_resource(res_src, res_update_data, dep_src, dep_update_data):
    for key, value in res_update_data.items():
            if value.has_key(TAG_UPDATED):
                del value[TAG_UPDATED]
                res_src.update({key: value})

    dep_src = dict([(key, dep_update_data[key]) for key in res_src.keys()])
    return res_src, dep_src
