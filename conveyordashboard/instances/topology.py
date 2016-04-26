#    Copyright (c) 2014 Mirantis, Inc.
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

import json

from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.urlresolvers import reverse
from django.template import loader

from conveyordashboard.api import api


def _truncate_type(type_str, num_of_chars):
    if len(type_str) < num_of_chars:
        return type_str
    else:
        parts = type_str.split('.')
        type_str, type_len = parts[-1], len(parts[-1])
        for part in reversed(parts[:-1]):
            if type_len + len(part) + 1 > num_of_chars:
                return '...' + type_str
            else:
                type_str = part + '.' + type_str
                type_len += len(part) + 1
        return type_str


def _unit_info(unit, unit_image):
    data = dict(unit)
    data['type'] = _truncate_type(data['type'], 45)
    context = {'data': data,
               'unit_image': unit_image}

    return loader.render_to_string('plans/_unit_info.html', context)


def _plan_info(plan_id, status, **kwargs):
    context = {'id': plan_id,
               'status': status}
    context.update(kwargs)
    return loader.render_to_string('instances/_plan_info.html',
                                   context)


def _create_empty_node(image_size=50):
    if isinstance(image_size, int):
        image_size = 50
    node = {
        'name': '',
        'status': 'ready',
        'image': '',
        'image_size': image_size,
        'required_by': [],
        'image_x': -image_size/2,
        'image_y': -image_size/2,
        'text_x': 40,
        'text_y': ".35em",
        'link_type': "relation",
        'in_progress': False,
        'info_box': ''
    }
    return node


def render_d3_data(request, plan_id, resource_dependencies, **kwargs):
    d3_data = {"nodes": [], "environment": {}}

    in_progress, status_message = True, 'Clone Plan'
    plan_node = _create_empty_node()
    plan_node.update({
        'id': plan_id,
        'status': status_message,
        'image': static('conveyordashboard/img/plan.png'),
        'in_progress': in_progress,
        'info_box': _plan_info(plan_id, status_message, **kwargs)
    })
    d3_data['environment'] = plan_node

    node_refs = {}

    #resource_dependencies = plan.resource_dependencies
    for service in resource_dependencies.values():
        in_progress, status_message = True, 'Node Topology'
        
        service_node = _create_empty_node()
        service_image = api.get_resource_image(service['type'])
        node_id = service['name_in_template']
        node_refs[node_id] = service_node
        service_node.update({
            'name': service['name'],
            'status': status_message,
            'image': service_image,
            'id': node_id,
            'type': service['type'],
            'link_type': 'relation',
            'in_progress': in_progress,
            'info_box': _unit_info(service, service_image)
        })
        if service['dependencies']:
            for dependency in service['dependencies']:
                service_node['required_by'].append(dependency)
        d3_data['nodes'].append(service_node)

    return json.dumps(d3_data)


def load_plan_d3_data(request, plan, is_original=True):
    if (not hasattr(plan, "updated_dependencies") 
        or not plan.updated_dependencies):
        return render_d3_data(request, plan.plan_id,
                                       plan.original_dependencies)
    else:
        return render_d3_data(request, plan.plan_id,
                                       plan.updated_dependencies)


def load_d3_data(request, plan_id, resource_dependencies, **kwargs):
    return render_d3_data(request, plan_id, resource_dependencies, **kwargs)
