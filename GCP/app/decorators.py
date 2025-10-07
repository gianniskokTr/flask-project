import google.auth.transport.requests
from google.oauth2 import id_token
from functools import wraps
from flask import request, abort
from flask_login import current_user
import logging

def google_authenticated(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            abort(401)

        token_parts = auth_header.split(" ")
        token = token_parts[1] if len(token_parts) > 1 else None

        try:
            id_token.verify_token(token, google.auth.transport.requests.Request())
        except Exception as e:
            logging.error(f"Authentication denied: {e}")
            abort(401)

        return func(*args, **kwargs)

    return decorated_function

def admin_required(func):
    @wraps(func)
    def check_roles(*args, **kwargs):
        is_admin = current_user.is_admin
        if not is_admin:
            abort(403)
        return func(*args, **kwargs)
    return check_roles
