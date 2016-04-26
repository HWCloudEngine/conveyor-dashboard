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
        LOG.debug('no conveyor service configured.')
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
