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

from conveyordashboard.overview import views


urlpatterns = patterns(
    'conveyordashboard.overview.views',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^row_actions$', views.RowActionsView.as_view(), name='row_actions'),
    url(r'^table_actions$',
        views.TableActionsView.as_view(), name='table_actions'),
)
