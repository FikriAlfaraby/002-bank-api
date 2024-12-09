from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from flasgger.utils import swag_from
from app.models import User
from datetime import timedelta
import re

bp = Blueprint('users', __name__, url_prefix='/users')

@bp.route('', methods=['POST'])
@swag_from({
    'tags': ['Users'],
    'summary': 'Create a new user',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string'},
                    'email': {'type': 'string'},
                    'password': {'type': 'string'}
                },
                'required': ['username', 'email', 'password']
            }
        }
    ],
    'responses': {
        201: {'description': 'User created successfully'},
        400: {'description': 'Invalid input'}
    }
})
def create_user():
    data = request.json

    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already exists."}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already exists."}), 400

    if not re.match(r"[^@]+@[^@]+\.[^@]+", data['email']):
        return jsonify({"error": "Invalid email format."}), 400

    if len(data['password']) < 8:
        return jsonify({"error": "Password must be at least 8 characters long."}), 400

    hashed_password = generate_password_hash(data['password'])
    user = User(username=data['username'], email=data['email'], password_hash=hashed_password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User created successfully"}), 201

@bp.route('/login', methods=['POST'])
@swag_from({
    'tags': ['Users'],
    'summary': 'User login',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string'},
                    'password': {'type': 'string'}
                },
                'required': ['username', 'password']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Login successful',
            'schema': {
                'type': 'object',
                'properties': {
                    'access_token': {'type': 'string'}
                }
            }
        },
        401: {'description': 'Invalid username or password'}
    }
})
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        access_token = create_access_token(identity=str(user.id), expires_delta=timedelta(hours=1))
        return jsonify({"access_token": access_token}), 200
    return jsonify({"error": "Invalid username or password"}), 401

@bp.route('/me', methods=['GET'])
@jwt_required()
@swag_from({
    'tags': ['Users'],
    'summary': 'Get user profile',
    'security': [{'JWT': []}],
    'responses': {
        200: {
            'description': 'User profile retrieved successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'username': {'type': 'string'},
                    'email': {'type': 'string'},
                    'created_at': {'type': 'string'},
                    'updated_at': {'type': 'string'}
                }
            }
        },
        401: {'description': 'Unauthorized'}
    }
})
def get_user_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at" : user.created_at,
        "updated_at" : user.updated_at
    })

@bp.route('/me', methods=['PUT'])
@jwt_required()
@swag_from({
    'tags': ['Users'],
    'summary': 'Update user profile',
    'security': [{'JWT': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string'},
                    'email': {'type': 'string'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Profile updated successfully'},
        401: {'description': 'Unauthorized'},
        400: {'description': 'Invalid input'}
    }
})
def update_user_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.json
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    db.session.commit()
    return jsonify({"message": "Profile updated successfully"})

@bp.route('/change-password', methods=['PUT'])
@jwt_required()
@swag_from({
    'tags': ['Users'],
    'summary': 'Change user password',
    'security': [{'JWT': []}],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'old_password': {'type': 'string'},
                    'new_password': {'type': 'string'}
                },
                'required': ['old_password', 'new_password']
            }
        }
    ],
    'responses': {
        200: {'description': 'Password changed successfully'},
        401: {'description': 'Unauthorized'},
        400: {'description': 'Invalid input'}
    }
})
def change_password():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    data = request.json

    if not check_password_hash(user.password_hash, data['old_password']):
        return jsonify({"error": "Old password is incorrect."}), 401

    if len(data['new_password']) < 8:
        return jsonify({"error": "New password must be at least 8 characters long."}), 400

    user.password_hash = generate_password_hash(data['new_password'])
    db.session.commit()
    return jsonify({"message": "Password changed successfully"})

