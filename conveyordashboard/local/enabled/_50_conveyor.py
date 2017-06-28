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

ADD_ANGULAR_MODULES = ['horizon.app.conveyor']

AUTO_DISCOVER_STATIC_FILES = True
