import logging

from flask import request, jsonify
from flask_login import login_user, logout_user, login_required, current_user

from app.models import User, logger
from app.auth import bp as auth_bp
from app.exceptions import UserAlreadyExistsError
from app.decorators import google_authenticated

@auth_bp.route('/register', methods=['POST'])
@google_authenticated
def register():
    data = request.get_json()
    if not data:
        return jsonify({"message": 'Invalid JSON'}), 400
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    is_admin = data.get("is_admin") # yy malakies kanw alla thelw na testarw
    if not username or not email or not password:
        return jsonify({"message": 'Missing required fields'}), 400
    try:
        user = User.create_user(username=username, email=email, password=password, is_admin=is_admin)
        return jsonify({"model": user.kind(), "key_id": user.id()}), 201
    except UserAlreadyExistsError as e:
        return jsonify({"message": str(e)}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"message": 'Invalid JSON'}), 400
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"message": 'Missing required fields'}), 400
    user = User.get_by_username(username)
    if not user or not user.check_password(password):
        return jsonify({"message": 'Invalid credentials'}), 401
    login_user(user)
    return jsonify({
        "message": 'Login successful',
        "user": user.to_dict()
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": 'Logout successful'}), 200

@auth_bp.route('/user', methods=['GET'])
@login_required
def get_user():
    return jsonify({"user": current_user.to_dict()}), 200


