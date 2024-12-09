from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
from app import db
from app.models import Account

bp = Blueprint('accounts', __name__, url_prefix='/accounts')

@bp.route('', methods=['GET'])
@jwt_required()
@swag_from({
    "tags": ["Accounts"],
    "summary": "Get all accounts",
    "description": "Retrieve all accounts for the authenticated user.",
    "security": [{"JWT": []}],
    "responses": {
        "200": {
            "description": "A list of user accounts",
            "schema": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "example": 1},
                        "account_type": {"type": "string", "example": "Savings"},
                        "account_number": {"type": "string", "example": "1234567890"},
                        "balance": {"type": "number", "format": "float", "example": 1000.50}
                    }
                }
            }
        },
        "401": {"description": "Unauthorized"}
    }
})
def get_all_accounts():
    user_id = get_jwt_identity()
    accounts = Account.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "id": account.id,
        "account_type": account.account_type,
        "account_number": account.account_number,
        "balance": float(account.balance)
    } for account in accounts])


@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
@swag_from({
    "tags": ["Accounts"],
    "summary": "Get account by ID",
    "description": "Retrieve an account by its ID for the authenticated user.",
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "The account ID"
        }
    ],
    "security": [{"JWT": []}],
    "responses": {
        "200": {
            "description": "Account details",
            "schema": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "account_type": {"type": "string", "example": "Savings"},
                    "account_number": {"type": "string", "example": "1234567890"},
                    "balance": {"type": "number", "format": "float", "example": 1000.50}
                }
            }
        },
        "404": {"description": "Account not found"},
        "401": {"description": "Unauthorized"}
    }
})
def get_account(id):
    user_id = get_jwt_identity()
    account = Account.query.filter_by(id=id, user_id=user_id).first()
    if not account:
        return jsonify({"error": "Account not found"}), 404
    return jsonify({
        "id": account.id,
        "account_type": account.account_type,
        "account_number": account.account_number,
        "balance": float(account.balance)
    })


@bp.route('', methods=['POST'])
@jwt_required()
@swag_from({
    "tags": ["Accounts"],
    "summary": "Create a new account",
    "description": "Create a new account for the authenticated user. Ensures that the account number is unique.",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "account_type": {"type": "string", "example": "savings"},
                    "account_number": {"type": "string", "example": "1234567890"},
                    "balance": {"type": "number", "format": "float", "example": 5000.0}
                },
                "required": ["account_type", "account_number"]
            }
        }
    ],
    "security": [{"JWT": []}],
    "responses": {
        "201": {
            "description": "Account created successfully",
            "schema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "example": "Account created successfully"}
                }
            }
        },
        "400": {
            "description": "Validation error (e.g., account number already exists)",
            "schema": {
                "type": "object",
                "properties": {
                    "error": {"type": "string", "example": "Account number already exists"}
                }
            }
        },
        "401": {
            "description": "Unauthorized",
            "schema": {
                "type": "object",
                "properties": {
                    "error": {"type": "string", "example": "Missing Authorization Header"}
                }
            }
        }
    }
})
def create_account():
    user_id = get_jwt_identity()
    data = request.json

    if not data['account_number'].isdigit() or len(data['account_number']) < 10:
        return jsonify({"error": "Account number must be at least 10 digits and numeric."}), 400

    existing_account = Account.query.filter_by(account_number=data['account_number']).first()
    if existing_account:
        return jsonify({"error": "Account number already exists"}), 400

    balance = data.get('balance', 0.0)
    if balance < 0:
        return jsonify({"error": "Initial balance cannot be negative."}), 400

    account = Account(
        user_id=user_id,
        account_type=data['account_type'],
        account_number=data['account_number'],
        balance=balance
    )
    db.session.add(account)
    db.session.commit()
    return jsonify({"message": "Account created successfully"}), 201


@bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@swag_from({
    "tags": ["Accounts"],
    "summary": "Update account by ID",
    "description": "Update the details of an existing account by its ID. Authorization is required for the account owner.",
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "The ID of the account to update",
            "example": 1
        },
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "account_type": {"type": "string", "example": "Savings"},
                    "balance": {"type": "number", "format": "float", "example": 500.00}
                },
                "required": ["account_type"]
            }
        }
    ],
    "security": [{"JWT": []}],
    "responses": {
        "200": {"description": "Account updated successfully"},
        "404": {"description": "Account not found"},
        "400": {"description": "Invalid input"}
    }
})
def update_account(id):
    user_id = get_jwt_identity()
    account = Account.query.filter_by(id=id, user_id=user_id).first()
    if not account:
        return jsonify({"error": "Account not found"}), 404

    data = request.json
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid input"}), 400

    account.account_type = data.get('account_type', account.account_type)
    
    if 'balance' in data:
        new_balance = data['balance']
        if new_balance < 0:
            return jsonify({"error": "Balance cannot be negative."}), 400
        account.balance = new_balance

    db.session.commit()
    return jsonify({"message": "Account updated successfully"}), 200

@bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@swag_from({
    "tags": ["Accounts"],
    "summary": "Delete account by ID",
    "description": "Delete an existing account by its ID. Authorization is required for the account owner.",
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "The ID of the account to delete",
            "example": 1
        }
    ],
    "security": [{"JWT": []}],
    "responses": {
        "200": {"description": "Account deleted successfully"},
        "404": {"description": "Account not found"}
    }
})
def delete_account(id):
    user_id = get_jwt_identity()
    account = Account.query.filter_by(id=id, user_id=user_id).first()
    if not account:
        return jsonify({"error": "Account not found"}), 404

    db.session.delete(account)
    db.session.commit()
    return jsonify({"message": "Account deleted successfully"}), 200

