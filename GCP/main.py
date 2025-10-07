from flask import jsonify
from flask_login import LoginManager
from app import create_app


login = LoginManager()
login.login_view = 'auth.login'
app = create_app()

login.init_app(app)

from app.core import bp as main_bp
from app.auth import bp as auth_bp
from app.models import User

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)

@app.errorhandler(Exception)
def handle_generic_exception(error):
    return jsonify({"message": str(error)}), 500

@login.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)