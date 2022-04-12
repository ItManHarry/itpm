from flask import url_for, redirect
from pm.utils import get_time, format_time, get_current_user, get_current_module, get_current_menu
def register_webapp_global_path(app):
    '''
    注册系统全局路径
    :param app:
    :return:
    '''
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
    @app.before_request
    def request_intercept_before():
        print('Before the request...')
        pass
def register_webapp_global_context(app):
    '''
    注册系统全局上下文(后台&前台页面均可用)
    :param app:
    :return:
    '''
    @app.context_processor
    def config_template_context():
        return dict(get_time=get_time,
                    format_time=format_time,
                    get_current_user=get_current_user,
                    get_current_module=get_current_module,
                    get_current_menu=get_current_menu)