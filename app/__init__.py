from flask import Flask
from config import config
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager
from flask_moment import Moment

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
bootstrap = Bootstrap5()
moment = Moment()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    bootstrap.init_app(app)
    login_manager.init_app(app)
    moment.init_app(app)

    # todo
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')


    return app


