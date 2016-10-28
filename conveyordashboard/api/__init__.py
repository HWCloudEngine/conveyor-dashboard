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

import logging

from django.conf import settings

from horizon import exceptions
from horizon.utils.memoized import memoized  # noqa

from openstack_dashboard.api import base

from conveyorclient import client

LOG = logging.getLogger(__name__)


def _get_endpoint(request):
    try:
        endpoint = base.url_for(request, 'conveyor')
        return endpoint
    except exceptions.ServiceCatalogException:
        LOG.debug('No conveyor service configured.')
        raise


def conveyorclient(request):
    endpoint = _get_endpoint(request)
    insecure = True
    getattr(settings, 'CONVEYOR_API_INSECURE', False)

    token_id = request.user.token.id
    c = client.Client(1, endpoint=endpoint, token=token_id,
                      insecure=insecure)
    c.client.auth_token = request.user.token.id
    c.client.management_url = endpoint
    return c
