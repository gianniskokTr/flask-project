from flask import Flask, jsonify
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from google.appengine.api import wrap_wsgi_app
from app import exceptions

def create_app():
    app = Flask(__name__)

    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "Stores REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["JWT_SECRET_KEY"] = "test_key"

    api = Api(app)
    jwt = JWTManager(app)

    from app.main import bp as main_bp

    app.register_blueprint(main_bp)

    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        return jsonify({"message": "Internal server error"}), 500

    app.wsgi_app = wrap_wsgi_app(app.wsgi_app)

    return app

from app import models

