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

PLAN = r'^(?P<plan_id>[^/]+)/%s$'

urlpatterns = patterns(
    'conveyordashboard.plans.views',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^clone$', views.CloneView.as_view(), name='clone'),
    url(r'^migrate$', views.MigrateView.as_view(), name='migrate'),
    url(r'^import$', views.ImportView.as_view(), name='import'),
    url(PLAN % '', views.DetailView.as_view(), name='detail'),
    url(PLAN % 'save', views.SaveView.as_view(), name='save'),
    url(PLAN % 'modify', views.ModifyView.as_view(), name='modify'),
    url(PLAN % 'export', views.ExportView.as_view(), name='export'),
    url(PLAN % 'destination', views.DestinationView.as_view(),
        name='destination'),

    url(r'^get_local_topology$',
        views.LocalTopologyView.as_view(), name='local_topology'),
    url(r'^get_global_topology$',
        views.GlobalTopologyView.as_view(), name='global_topology')
)
