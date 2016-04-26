from openstack_dashboard.api import base


class Server(base.APIDictWrapper):
    _attrs = ['addresses', 'attrs', 'id', 'image', 'links', 'metadata', 'name',
              'private_ip', 'public_ip', 'status', 'uuid', 'image_name',
              'VirtualInterfaces', 'flavor', 'key_name', 'fault', 'tenant_id',
              'user_id', 'created', 'OS-EXT-STS:power_state',
              'OS-EXT-STS:task_state', 'OS-EXT-SRV-ATTR:instance_name',
              'OS-EXT-SRV-ATTR:host', 'OS-EXT-AZ:availability_zone',
              'OS-DCF:diskConfig']


class Flavor(base.APIDictWrapper):
    _attrs = [ 'ram', 'vcpus', 'disk', 'swap', 'ephemeral','rxtx_factor', 
              'extra_specs', 'is_public']


class Resource(base.APIDictWrapper):
    """
    """