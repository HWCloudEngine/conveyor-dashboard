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

import netaddr
import uuid

from django.conf import settings
from django.utils.translation import ugettext_lazy as _


def _clean_rule_icmp(cleaned_data, rule_menu):
    icmp_type = cleaned_data.get("icmp_type", None)
    icmp_code = cleaned_data.get("icmp_code", None)
    cleaned_data['ip_protocol'] = rule_menu

    if icmp_type == -1 and icmp_code != -1:
        msg = _('ICMP code is provided but ICMP type is missing.')
        raise Exception(msg)

    cleaned_data['from_port'] = icmp_type
    cleaned_data['to_port'] = icmp_code
    cleaned_data['port'] = None


def _clean_rule_tcp_udp(cleaned_data, rule_menu):
    port_or_range = cleaned_data.get("port_or_range")
    from_port = cleaned_data.get("from_port", None)
    to_port = cleaned_data.get("to_port", None)
    port = cleaned_data.get("port", None)

    cleaned_data['ip_protocol'] = rule_menu
    cleaned_data['icmp_code'] = None
    cleaned_data['icmp_type'] = None

    if port_or_range == "port":
        cleaned_data['from_port'] = port
        cleaned_data['to_port'] = port
        if port is None:
            msg = _('The specified port is invalid.')
            raise Exception(msg)
    else:
        cleaned_data['port'] = None
        if from_port is None:
            msg = _('The "from" port number is invalid.')
            raise Exception(msg)
        if to_port is None:
            msg = _('The "to" port number is invalid.')
            raise Exception(msg)
        if to_port < from_port:
            msg = _('The "to" port number must be greater than '
                    'or equal to the "from" port number.')
            raise Exception(msg)


def _clean_rule_custom(cleaned_data, rule_menu):
    # custom IP protocol rule so we need to fill unused fields so
    # the validation works
    cleaned_data['icmp_code'] = None
    cleaned_data['icmp_type'] = None


def _apply_rule_menu(cleaned_data, rule_menu):
    rules = getattr(settings, 'SECURITY_GROUP_RULES', [])
    cleaned_data['ip_protocol'] = rules[rule_menu]['ip_protocol']
    cleaned_data['from_port'] = int(rules[rule_menu]['from_port'])
    cleaned_data['to_port'] = int(rules[rule_menu]['to_port'])
    cleaned_data['icmp_code'] = None
    cleaned_data['icmp_type'] = None
    if rule_menu not in ['all_tcp', 'all_udp', 'all_icmp']:
        direction = rules[rule_menu].get('direction')
        cleaned_data['direction'] = direction


def _clean_rule_menu(cleaned_data):
    rule_menu = cleaned_data.get('rule_menu')
    if rule_menu == 'icmp':
        _clean_rule_icmp(cleaned_data, rule_menu)
    elif rule_menu == 'tcp' or rule_menu == 'udp':
        _clean_rule_tcp_udp(cleaned_data, rule_menu)
    elif rule_menu == 'custom':
        _clean_rule_custom(cleaned_data, rule_menu)
    else:
        _apply_rule_menu(cleaned_data, rule_menu)


def generate_rule(rule_param):
    _clean_rule_menu(rule_param)
    remote = rule_param.get("remote")
    if remote == "cidr":
        rule_param['security_group'] = None
    else:
        rule_param['cidr'] = None

    if not rule_param['direction']:
        rule_param['direction'] = 'ingress'

    # If cleaned_data does not contain a non-empty value, IPField already
    # has validated it, so skip the further validation for cidr.
    # In addition cleaned_data['cidr'] is None means source_group is used.
    if 'cidr' in rule_param and rule_param['cidr'] is not None:
        cidr = rule_param['cidr']
        if not cidr:
            msg = _('CIDR must be specified.')
            raise Exception(msg)
        else:
            # If cidr is specified, ethertype is determined from IP address
            # version. It is used only when Neutron is enabled.
            ip_ver = netaddr.IPNetwork(cidr).version
            rule_param['ethertype'] = 'IPv6' if ip_ver == 6 else 'IPv4'

    rule = {}
    rule['id'] = str(uuid.uuid4())
    rule['direction'] = rule_param['direction']
    rule['protocol'] = rule_param['ip_protocol']
    rule['port_range_min'] = rule_param['from_port']
    rule['port_range_max'] = rule_param['to_port']

    rule['remote_group_id'] = rule_param['security_group']
    rule['remote_ip_prefix'] = rule_param['cidr']
    # rule['security_group_id'] = rule_param['security_group']
    if 'from_port' in rule_param and rule_param['from_port'] != -1:
        rule['port_range_min'] = rule_param['from_port']
    if 'to_port' in rule_param and rule_param['to_port'] != -1:
        rule['port_range_max'] = rule_param['to_port']

    return rule
