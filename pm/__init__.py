from flask import Flask
from pm.configs import configurations
from pm.regs.web_errors import register_webapp_errors
from pm.regs.web_globals import register_webapp_global_context, register_webapp_global_path
from pm.regs.web_plugins import register_webapp_plugins
from pm.regs.web_views import register_webapp_views
from pm.regs.web_shells import register_webapp_shell, register_webapp_commands

def create_app(config=None):
    if(config == None):
        config = 'dev_config'
    app = Flask('pm')
    app.config.from_object(configurations[config])
    register_webapp_plugins(app)
    register_webapp_global_path(app)
    register_webapp_global_context(app)
    register_webapp_errors(app)
    register_webapp_views(app)
    register_webapp_shell(app)
    register_webapp_commands(app)
    return app