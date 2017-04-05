# Copyright (c) 2017 Huawei, Inc.
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
from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from horizon.utils import functions as utils
from openstack_dashboard import api as os_api
from oslo_log import log as logging

from conveyordashboard import api
from conveyordashboard.api import models
from conveyordashboard.common import constants as consts

RESOURCE_TYPE_IMAGE_MAPPINGS = consts.RESOURCE_TYPE_IMAGE_MAPPINGS

LOG = logging.getLogger(__name__)


def get_resource_image(res_type, color='green'):
    if res_type not in RESOURCE_TYPE_IMAGE_MAPPINGS:
        res_type = 'UNKNOWN'
    url = static(
        consts.IMAGE_DIR + RESOURCE_TYPE_IMAGE_MAPPINGS[res_type][color])
    return url


def plan_list(request, search_opts=None):
    return api.conveyorclient(request).plans.list(search_opts)


def plan_create(request, plan_type, resource):
    return api.conveyorclient(request).plans.create(plan_type, resource)


def plan_delete(request, plan_id):
    return api.conveyorclient(request).plans.delete(plan_id)


def plan_get(request, plan_id):
    return api.conveyorclient(request).plans.get(plan_id)


def update_plan_resource(request, plan, resources):
    return api.conveyorclient(request).plans.update_plan_resource(plan,
                                                                  resources)


def download_template(request, plan_id):
    LOG.info("Download_template %s" % plan_id)
    return api.conveyorclient(request).plans.download_template(plan_id)


def create_plan_by_template(request, template):
    return api.conveyorclient(request).plans.create_plan_by_template(template)


def resource_list(request, resource_type, search_opts=None):
    if not search_opts:
        search_opts = {}
    search_opts['type'] = resource_type
    return api.conveyorclient(request).resources.list(search_opts)


def resource_get(request, id, plan_id):
    return api.conveyorclient(request).resources.get(id, plan_id)


def resource_detail(request, res_type, res_id):
    return api.conveyorclient(request).resources.get_resource_detail(res_type,
                                                                     res_id)


def resource_detail_from_plan(request, id, plan_id, is_original=True):
    return api.conveyorclient(request).resources\
        .get_resource_detail_from_plan(id, plan_id, is_original)


def export_clone_template(request, plan_id, sys_clone=False):
    return api.conveyorclient(request).clones.export_clone_template(
        plan_id, sys_clone=sys_clone)


def clone(request, plan_id, destination):
    return api.conveyorclient(request).clones.clone(plan_id, destination)


def export_template_and_clone(request, plan, destination,
                              resources={},
                              sys_clone=False):
    return api.conveyorclient(request).clones.export_template_and_clone(
        plan, destination, resources, sys_clone
    )


def export_migrate_template(request, plan_id):
    return api.conveyorclient(request)\
        .migrates.export_migrate_template(plan_id)


def migrate(request, plan_id, destination):
    return api.conveyorclient(request).migrates.migrate(plan_id, destination)


def server_list(request, search_opts=None, all_tenants=False):
    page_size = utils.get_page_size(request)
    paginate = False
    if search_opts is None:
        search_opts = {}
    elif 'paginate' in search_opts:
        paginate = search_opts.pop('paginate')
        if paginate:
            search_opts['limit'] = page_size + 1

    if all_tenants:
        search_opts['all_tenants'] = True
    else:
        search_opts['project_id'] = request.user.tenant_id
    servers = [s for s in resource_list(request,
                                        consts.NOVA_SERVER,
                                        search_opts)]

    has_more_data = False
    if paginate and len(servers) > page_size:
        servers.pop(-1)
        has_more_data = True
    elif paginate and len(servers) == getattr(settings, 'API_RESULT_LIMIT',
                                              1000):
        has_more_data = True
    return ([os_api.nova.Server(i, request) for i in servers],
            has_more_data)


def server_get(request, id):
    return models.Server(resource_detail(request, consts.NOVA_SERVER, id))


def availability_zone_list(request, detailed=False):
    azs = resource_list(request, consts.NOVA_AZ)
    if not detailed:
        azs = [az for az in azs if az.zoneName != 'internal']
    return azs


def flavor_get(request, id):
    return models.Flavor(resource_detail(request, consts.NOVA_FLAVOR, id))


def net_get(request, id):
    network = resource_detail(request, consts.NEUTRON_NET, id)
    return os_api.neutron.Network(network)


def net_list(request, search_opts=None):
    networks = resource_list(request, consts.NEUTRON_NET,
                             search_opts=search_opts)
    subnets = resource_list(request, consts.NEUTRON_SUBNET)
    subnet_dict = dict([(s.id, s) for s in subnets])
    for n in networks:
        setattr(n, 'subnets',
                [subnet_dict[s] for s in getattr(n, 'subnets', [])
                 if s in subnet_dict])
    return networks


def net_list_for_tenant(request, tenant_id, search_opts=None):
    nets = net_list(request, search_opts)
    return [os_api.neutron.Network(n.__dict__) for n in nets
            if n.tenant_id == tenant_id]


def subnet_list_for_tenant(request, tenant_id, search_opts=None):
    subnets = resource_list(request, consts.NEUTRON_SUBNET,
                            search_opts=search_opts)
    return [os_api.neutron.Subnet(sn.__dict__) for sn in subnets
            if sn.tenant_id == tenant_id]


def subnet_list_for_network(request, tenant_id=None, is_external=False):
    nets = net_list(request) \
        if not tenant_id else net_list_for_tenant(request, tenant_id)
    nets = [n for n in nets if getattr(n, 'router:external') == is_external]

    subnets = []
    for n in nets:
        for sn in getattr(n, 'subnets'):
            if sn not in subnets:
                subnets.append(sn)
    return subnets


def sg_list(request, tenant_id=None, search_opts=None):
    secgroups = resource_list(request, consts.NEUTRON_SECGROUP,
                              search_opts=search_opts)
    sgs = [sg.__dict__ for sg in secgroups if sg.tenant_id == tenant_id]
    return [os_api.neutron.SecurityGroup(sg) for sg in sgs]


def sg_get(request, sg_id):
    secgroup = resource_detail(request, consts.NEUTRON_SECGROUP, sg_id)
    return os_api.neutron.SecurityGroup(secgroup)


def pool_list(request, **kwargs):
    pools = [p.get('pools') for p in
             resource_list(request, consts.NEUTRON_POOL)]
    return [os_api.lbaas.Pool(p) for p in pools]


class ResourceDetail(object):
    """Wrap dict response to class."""

    def __init__(self, request, res_type, res_id, **kwargs):
        self.request = request
        self.res_type = res_type
        self.res_id = res_id
        self.kwargs = kwargs

    def _get_server(self):
        return server_get(self.request, self.res_id)

    def get(self):
        method = ''.join(('_get_', self.res_type.split('::')[-1].lower()))
        LOG.info("Method={0}".format(method))
        if hasattr(self, method):
            return getattr(self, method)()
        else:
            return models.Resource(resource_detail(self.request,
                                                   self.res_type,
                                                   self.res_id))
