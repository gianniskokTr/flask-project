from flask import Flask, jsonify
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from google.appengine.api import wrap_wsgi_app

from app import exceptions

login = LoginManager()
jwt = JWTManager()
login.login_view = 'auth.login'

def create_app():
    app = Flask(__name__)

    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["JWT_SECRET_KEY"] = "test_key"
    app.config['SECRET_KEY'] = 'ti-egine-kwstaki-se-goustarei-i-xwriatisa'

    login.init_app(app)
    jwt.init_app(app)

    from app.core import bp as main_bp
    from app.auth import bp as auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        return jsonify({"message": str(error)}), 500

    app.wsgi_app = wrap_wsgi_app(app.wsgi_app)

    return app

from app import models
