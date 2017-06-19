from django.conf import settings

from conveyordashboard import exceptions

# The name of the dashboard to be added to HORIZON['dashboards']. Required.
DASHBOARD = 'conveyor'

# If set to True, this dashboard will not be added to the settings.
DISABLED = False

ADD_INSTALLED_APPS = [
    'conveyordashboard'
]

ADD_EXCEPTIONS = {
    'recoverable': exceptions.RECOVERABLE,
    'not_found': exceptions.NOT_FOUND,
    'unauthorized': exceptions.UNAUTHORIZED,
}

ADD_JS_FILES = [
    'conveyordashboard/js/lib/jquery.cookie.js',
    'conveyordashboard/js/lib/jquery.treeTable.js',
    'conveyordashboard/js/lib/json2.js',
    'conveyordashboard/js/conveyor.utils.js',
    'conveyordashboard/js/conveyor.service.js',
    'conveyordashboard/js/edit_plan_res.js',
    'conveyordashboard/js/deps_table.js',
    'conveyordashboard/js/conveyor.selector.js',
    'conveyordashboard/js/conveyor.resource.js',
    'conveyordashboard/js/clone_plan_form.js',
    'conveyordashboard/js/migrate_plan_form.js',
    'conveyordashboard/js/save_plan_form.js',
    'conveyordashboard/js/destination_form.js',
]

if getattr(settings, 'CONVEYOR_USE_ACTION_PLUGIN', False):
    ADD_JS_FILES.append('conveyordashboard/js/conveyor.actions.plugin.js')
