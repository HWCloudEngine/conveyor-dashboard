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

import json

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
    data['dependencies'] = '[' + ', '.join(data['dependencies']) + ']'
    context = {'data': data,
               'unit_image': unit_image}

    return loader.render_to_string('plans/_unit_info.html', context)


def _create_empty_node(image_size=50):
    if isinstance(image_size, int):
        image_size = 50
    node = {
        'name': '',
        'status': 'ready',
        'image': '',
        'image_size': image_size,
        'required_by': [],
        'image_x': -image_size / 2,
        'image_y': -image_size / 2,
        'text_x': 40,
        'text_y': ".35em",
        'link_type': "relation",
        'in_progress': False,
        'info_box': ''
    }
    return node


def render_d3_data(request, resource_dependencies, **kwargs):
    d3_data = {'nodes': []}

    node_refs = {}

    # Resource_dependencies = plan.resource_dependencies.
    for dep in resource_dependencies.values():
        in_progress, status_message = True, 'Node Topology'

        service_node = _create_empty_node()
        service_image = api.get_resource_image(
            dep['type'],
            'green' if not dep.get('is_cloned') else 'gray')
        node_id = dep['name_in_template']
        node_refs[node_id] = service_node

        service_node.update({
            'name': dep['name'],
            'status': status_message,
            'image': service_image,
            'id': node_id,
            'type': dep['type'],
            'cloned': dep.get('is_cloned', False),
            'link_type': 'relation',
            'in_progress': in_progress,
            'info_box': _unit_info(dep, service_image)
        })
        if dep['dependencies']:
            for dependency in dep['dependencies']:
                service_node['required_by'].append(dependency)
        d3_data['nodes'].append(service_node)

    return json.dumps(d3_data)


def load_plan_d3_data(request, plan, plan_type, is_original=True):
    if plan_type == 'migrate' or not hasattr(plan, 'updated_dependencies') \
            or not plan.updated_dependencies:
        return render_d3_data(request, plan.original_dependencies)
    else:
        return render_d3_data(request, plan.updated_dependencies)


def load_d3_data(request, resource_dependencies, **kwargs):
    return render_d3_data(request, resource_dependencies, **kwargs)
