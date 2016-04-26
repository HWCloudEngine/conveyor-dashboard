from django.utils.translation import ugettext_lazy as _

from horizon import tables


class TriggersTable(tables.DataTable):
    # NOTE(gabriel): Commenting out the user column because all we have
    # is an ID, and correlating that at production scale using our current
    # techniques isn't practical. It can be added back in when we have names
    # returned in a practical manner by the API.
    # user = tables.Column("user_id", verbose_name=_("User"))
    class Meta(object):
        name = "triggers"
        verbose_name = _("Triggers")
        table_actions = ()
        row_actions = ()
