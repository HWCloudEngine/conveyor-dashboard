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

from django.core.urlresolvers import reverse
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _

from horizon import tables


def get_res_type(datum, table):
    if hasattr(datum, 'res_type'):
        return datum.res_type
    css_classes = table.css_classes()
    for css_cls in css_classes.split(' '):
        if css_cls.startswith('OS::'):
            return css_cls
    return ''


class CreatePlan(tables.LinkAction):
    name = 'create_plan'
    verbose_name = _("Create Plan")
    url = 'horizon:conveyor:plans:create'
    classes = ("ajax-modal",)

    def get_link_url(self, datum):
        base_url = reverse(self.url)

        params = urlencode({'ids': ''.join([get_res_type(datum, self.table),
                                            '*',
                                            self.table.get_object_id(datum)])})
        return '?'.join([base_url, params])


class CreatePlanWithMultiRes(tables.LinkAction):
    name = 'create_plan_with_mul_res'
    verbose_name = _("Create Plan")
    url = 'horizon:conveyor:plans:create'
    classes = ("ajax-modal", "disabled", "create-plan-with-multi-res")
    icon = 'plus'
