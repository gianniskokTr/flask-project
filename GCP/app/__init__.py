from flask import Flask
from google.appengine.api import wrap_wsgi_app


def create_app():
    app = Flask(__name__)

    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["JWT_SECRET_KEY"] = "test_key"
    app.config['SECRET_KEY'] = 'ti-egine-kwstaki-se-goustarei-i-xwriatisa'

    app.wsgi_app = wrap_wsgi_app(app.wsgi_app)

    return app


from app import exceptions
from app import models
from app import decorators
