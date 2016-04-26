import base64
import json
import logging
import six

from oslo_utils import encodeutils

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from conveyordashboard.api import api

LOG = logging.getLogger(__name__)


def preprocess_update_resources(update_resources):
    for resource in update_resources:
        if resource["type"] == "OS::Nova::Server":
            if resource.get("user_data", None):
                user_data = resource["user_data"]
                if six.PY3:
                    try:
                        user_data = user_data.encode("utf-8")
                    except AttributeError:
                        pass
                else:
                    try:
                        user_data = encodeutils.safe_encode(user_data)
                    except UnicodeDecodeError:
                        pass
                user_data = base64.b64encode(user_data).decode('utf-8')
                resource["user_data"] = user_data


class PlanForm(forms.SelfHandlingForm):
    def __init__(self, request, *args, **kwargs):
        super(PlanForm, self).__init__(request, *args, **kwargs)

    def handle(self, request, data):
        try:
            POST = request.POST
            plan_id = POST["plan_id"]
            plan_type = POST["plan_type"]
            update_resources = json.JSONDecoder().decode(POST["update_resource"])
            preprocess_update_resources(update_resources)
            LOG.info("PlanForm==>update_resources={}".format(update_resources))
            msg = ""
            if 'action_type' in POST \
                and POST['action_type'] in ["clone", "migrate", "cancel"]:
                if 'clone' == POST['action_type']:
                    az = POST.get("availability_zone", None)
                    host = POST.get("host", None)
                    api.clone(request, plan_id, az, update_resources)
                    msg = _('Succeed to clone instances to destination.'
                            'plan_id "%s".') % (plan_id)
                elif 'migrate' == POST["action_type"]:
                    az = POST.get("availability_zone", None)
                    host = POST.get("host", None)
                    msg = _('Succeed to Migrate instances to destination.'
                            'plan_id "%s".') % (plan_id)
                elif 'cancel' == POST['action_type']:
                    api.plan_delete(self.request, plan_id)
                    msg = _('Clone plan is cancelled to create.'
                        'plan_id "%s".') % (plan_id)
            else:
                api.export_clone_template(request, plan_id, update_resources)
                msg = _('Succeed to create %s plan to '
                        'plan_id "%s".') % (plan_type, plan_id)
            messages.success(request, msg)
            return True
        except Exception:
            msg = _('Some error occurs when processing plan host.')
            redirect = reverse('horizon:conveyor:instances:index')
            exceptions.handle(request, msg, redirect=redirect)


class ImportPlan(forms.SelfHandlingForm):
    def __init__(self, request, *args, **kwargs):
        super(ImportPlan, self).__init__(request, *args, **kwargs)

    def handle(self, request, data):
        try:
            plan_file = request.FILES['plan_upload']
            messages.success(request,
                             _('Successfully imported plan: %s')
                             % data['plan_upload'].name)
            return True
        except Exception:
            msg = _('Unable to import clone plan.')
            redirect = reverse('horizon:conveyor:plans:index')
            exceptions.handle(request, msg, redirect=redirect)
