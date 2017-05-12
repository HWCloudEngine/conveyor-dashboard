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
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from openstack_dashboard.dashboards.project.volumes.volumes import tables \
    as vol_tables

from conveyordashboard.api import api
from conveyordashboard.common import actions as common_actions
from conveyordashboard.common import constants as consts
from conveyordashboard.common import resource_state


class CloneVolume(common_actions.CreateClonePlan):
    def allowed(self, request, volume=None):
        if not volume:
            return False
        if volume.status not in resource_state.VOLUME_CLONE_STATE:
            return False
        return True


class MigrateVolume(common_actions.CreateMigratePlan):
    def allowed(self, request, volume=None):
        if not volume:
            return False
        if volume.status not in resource_state.VOLUME_MIGRATE_STATE:
            return False
        return True


class VolumeFilterAction(tables.FilterAction):
    def filter(self, table, volumes, filter_string):
        q = filter_string.lower()

        def comp(volume):
            return q in volume.name.lower()

        return filter(comp, volumes)


class UpdateVolumeRow(tables.Row):
    ajax = True

    def get_data(self, request, volume_id):
        volume = api.get_wrapped_detail_resource(request,
                                                 consts.CINDER_VOLUME,
                                                 volume_id)
        return volume


class VolumesTable(vol_tables.VolumesTable):
    class Meta(object):
        name = 'volumes'
        verbose_name = _("Volumes")
        css_classes = "table-res %s" % consts.CINDER_VOLUME
        status_columns = ["status"]
        row_class = UpdateVolumeRow
        table_actions = (common_actions.CreateClonePlanWithMulRes,
                         common_actions.CreateMigratePlanWithMulRes,
                         VolumeFilterAction)
        row_actions = (CloneVolume,
                       MigrateVolume,)
