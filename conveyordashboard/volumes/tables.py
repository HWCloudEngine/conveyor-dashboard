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

from django.template import defaultfilters as filters
from django.utils.translation import pgettext_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from conveyordashboard.common import actions as common_actions
from conveyordashboard.common import constants as consts
from conveyordashboard.common import resource_state


class CreatePlan(common_actions.CreatePlan):
    def allowed(self, request, volume=None):
        return volume.status in resource_state.VOLUME_CLONE_STATE


class VolumeFilterAction(tables.FilterAction):
    def filter(self, table, volumes, filter_string):
        q = filter_string.lower()

        def comp(volume):
            return q in volume.name.lower()

        return filter(comp, volumes)


def get_size(volume):
    return _("%sGiB") % volume.size


def get_volume_type(volume):
    return volume.volume_type if volume.volume_type != "None" else None


def get_encrypted_value(volume):
    if not hasattr(volume, 'encrypted') or volume.encrypted is None:
        return _("-")
    elif volume.encrypted is False:
        return _("No")
    else:
        return _("Yes")


class VolumesTableBase(tables.DataTable):
    STATUS_CHOICES = (
        ("available", True),
    )
    STATUS_DISPLAY_CHOICES = (
        ("available", pgettext_lazy("Current status of a Volume",
                                    u"Available")),
    )
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:project:volumes:volumes:detail")
    description = tables.Column("description",
                                verbose_name=_("Description"),
                                truncate=40)
    size = tables.Column(get_size,
                         verbose_name=_("Size"),
                         attrs={'data-type': 'size'})
    status = tables.Column("status",
                           verbose_name=_("Status"),
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)

    def get_object_display(self, obj):
        return obj.name


class VolumesFilterAction(tables.FilterAction):

    def filter(self, table, volumes, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [volume for volume in volumes
                if q in volume.name.lower()]


class VolumesTable(VolumesTableBase):
    name = tables.Column("name",
                         verbose_name=_("Name"),
                         link="horizon:project:volumes:volumes:detail")
    volume_type = tables.Column(get_volume_type,
                                verbose_name=_("Type"))
    availability_zone = tables.Column("availability_zone",
                                      verbose_name=_("Availability Zone"))
    bootable = tables.Column('is_bootable',
                             verbose_name=_("Bootable"),
                             filters=(filters.yesno, filters.capfirst))
    encryption = tables.Column(get_encrypted_value,
                               verbose_name=_("Encrypted"),
                               link="horizon:project:volumes:"
                                    "volumes:encryption_detail")

    class Meta(object):
        name = 'volumes'
        verbose_name = _("Volumes")
        css_classes = "table-res %s" % consts.CINDER_VOLUME
        status_columns = ["status"]
        table_actions = (common_actions.CreatePlanWithMultiRes,
                         VolumeFilterAction)
        row_actions = (CreatePlan,)
