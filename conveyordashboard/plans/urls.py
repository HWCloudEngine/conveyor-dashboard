# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

from django.conf.urls import patterns
from django.conf.urls import url

from conveyordashboard.plans import views

PLAN = r'^(?P<plan_id>[^/]+)/%s$'

urlpatterns = patterns(
    'conveyordashboard.plans.views',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(PLAN % '', views.DetailView.as_view(), name='detail'),
    url(r'^create$', views.CreateView.as_view(), name='create'),
    url(PLAN % 'cancel', views.CancelView.as_view(), name='cancel'),
    url(r'^import$', views.ImportView.as_view(), name='import'),
    url(PLAN % 'export', views.ExportView.as_view(), name='export'),
    url(PLAN % 'create_trigger', views.CreateTriggerView.as_view(),
        name='create_trigger'),
    url(PLAN % 'destination', views.DestinationView.as_view(),
        name='destination'),
    url(PLAN % 'update', views.UpdateView.as_view(), name='update'),
    url(r'^get_resource_detail$', views.ResourceDetailJsonView.as_view(),
        name='resource_detail'),
    url(r'^get_secgroup_rules/(?P<secgroup_id>[^/]+)$',
        views.SecgroupRulesView.as_view(),
        name='get_secgroup_rules'),
)
