# from conveyordashboard import exceptions

# The name of the dashboard to be added to HORIZON['dashboards']. Required.
DASHBOARD = 'conveyor'

# If set to True, this dashboard will not be added to the settings.
DISABLED = False

ADD_INSTALLED_APPS = [
    'conveyordashboard',
    'floppyforms'
]

ADD_JS_FILES = [
    'conveyordashboard/js/conveyor.field.js'
]

# ADD_EXCEPTIONS = {
#     'recoverable': exceptions.RECOVERABLE,
#     'not_found': exceptions.NOT_FOUND,
#     'unauthorized': exceptions.UNAUTHORIZED,
# }