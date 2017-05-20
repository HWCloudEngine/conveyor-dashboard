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

from django.conf.urls import patterns
from django.conf.urls import url

from conveyordashboard.plans import views
from conveyordashboard.topology import views as topology_views

PLAN = r'^(?P<plan_id>[^/]+)/%s$'
EDIT_PLAN_RES = r'^(?P<plan_id>[^/]+)/%s/(?P<res_id>[^/]+)$'

urlpatterns = patterns(
    'conveyordashboard.plans.views',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^clone$', views.CloneView.as_view(), name='clone'),
    url(r'^migrate$', views.MigrateView.as_view(), name='migrate'),
    url(r'^import$', views.ImportView.as_view(), name='import'),
    url(PLAN % '', views.DetailView.as_view(), name='detail'),
    url(PLAN % 'save', views.SaveView.as_view(), name='save'),
    url(PLAN % 'modify', views.ModifyView.as_view(), name='modify'),
    url(PLAN % 'cancel', views.CancelView.as_view(), name='cancel'),
    url(PLAN % 'export', views.ExportView.as_view(), name='export'),
    url(PLAN % 'destination', views.DestinationView.as_view(),
        name='destination'),
    url(PLAN % 'update_plan_resource', views.UpdatePlanResourceView.as_view(),
        name='update_plan_resource'),

    url(r'^get_resource_detail$', views.ResourceDetailJsonView.as_view(),
        name='resource_detail'),
    url(r'^get_secgroup_rules/(?P<secgroup_id>[^/]+)$',
        topology_views.SecgroupRulesView.as_view(),
        name='get_secgroup_rules'),
    url(r'^(?P<security_group_id>[^/]+)/add_rule/$',
        topology_views.AddRuleView.as_view(),
        name='add_rule'),
    url(r'^secgroup/(?P<secgroup_id>[^/]+)/create_rule/$',
        topology_views.CreateRuleView.as_view(),
        name='create_rule'),
    url(r'^get_local_topology$',
        topology_views.LocalTopologyView.as_view(), name='local_topology'),
    url(r'^get_global_topology$',
        topology_views.GlobalTopologyView.as_view(), name='global_topology'),

    # Edit plan resource
    url(EDIT_PLAN_RES % 'server', views.EditInstanceView.as_view(),
        name='edit_server'),
    url(EDIT_PLAN_RES % 'flavor', views.EditFlavorView.as_view(),
        name='edit_flavor'),
    url(EDIT_PLAN_RES % 'keypair', views.EditKeyPairView,
        name='edit_keypair'),
    url(EDIT_PLAN_RES % 'volume', views.EditVolumeView.as_view(),
        name='edit_volume'),
    url(EDIT_PLAN_RES % 'net', views.EditNetView.as_view(),
        name='edit_net'),
    url(EDIT_PLAN_RES % 'subnet', views.EditSubnetView.as_view(),
        name='edit_subnet'),
    url(EDIT_PLAN_RES % 'port', views.EditPortView.as_view(),
        name='edit_port'),
    url(EDIT_PLAN_RES % 'securitygroup', views.EditSecurityGroupView.as_view(),
        name='edit_securitygroup'),
)
