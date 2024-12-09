from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
from app import db
from app.models import Bill, Account
from datetime import datetime

bp = Blueprint('bills', __name__, url_prefix='/bills')

@bp.route('', methods=['POST'])
@jwt_required()
@swag_from({
    "tags": ["Bills"],
    "summary": "Create a new bill",
    "description": "Schedule a new bill for the authenticated user.",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "biller_name": {"type": "string", "example": "Electric Company"},
                    "due_date": {"type": "string", "format": "date", "example": "2023-12-31"},
                    "amount": {"type": "number", "format": "float", "example": 150.75},
                    "account_id": {"type": "integer", "example": 1}
                },
                "required": ["biller_name", "due_date", "amount", "account_id"]
            }
        }
    ],
    "security": [{"JWT": []}],
    "responses": {
        "201": {"description": "Bill scheduled successfully"},
        "400": {"description": "Invalid input"}
    }
})
def create_bill():
    user_id = get_jwt_identity()
    data = request.json

    amount = data['amount']
    if amount <= 0:
        return jsonify({"error": "Invalid amount. Amount must be greater than zero."}), 400

    due_date = data['due_date']
    try:
        due_date_obj = datetime.strptime(due_date, '%Y-%m-%d')
        if due_date_obj < datetime.now():
            return jsonify({"error": "Due date must be in the future."}), 400
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    account_id = data['account_id']
    account = Account.query.filter_by(id=account_id, user_id=user_id).first()
    if not account:
        return jsonify({"error": "Invalid account ID."}), 404

    bill = Bill(
        user_id=user_id,
        biller_name=data['biller_name'],
        due_date=due_date,
        amount=amount,
        account_id=account_id
    )
    db.session.add(bill)
    db.session.commit()
    return jsonify({"message": "Bill scheduled successfully"}), 201

@bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@swag_from({
    "tags": ["Bills"],
    "summary": "Update bill by ID",
    "description": "Update the details of a scheduled bill payment by its ID for the authenticated user.",
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "The bill ID"
        },
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "biller_name": {"type": "string", "example": "Electricity Company"},
                    "due_date": {"type": "string", "format": "date", "example": "2024-12-15"},
                    "amount": {"type": "number", "format": "decimal", "example": 150.75}
                },
                "required": ["biller_name", "due_date", "amount"]
            }
        }
    ],
    "security": [{"JWT": []}],
    "responses": {
        "200": {
            "description": "Bill updated successfully"
        },
        "404": {
            "description": "Bill not found"
        },
        "400": {
            "description": "Invalid input data"
        }
    }
})
def update_bill(id):
    user_id = get_jwt_identity()
    bill = Bill.query.filter_by(id=id, user_id=user_id).first()
    if not bill:
        return jsonify({"error": "Bill not found"}), 404

    data = request.json

    amount = data.get('amount', bill.amount)
    if amount <= 0:
        return jsonify({"error": "Invalid amount. Amount must be greater than zero."}), 400

    due_date = data.get('due_date', bill.due_date)
    try:
        due_date_obj = datetime.strptime(due_date, '%Y-%m-%d')
        if due_date_obj < datetime.now():
            return jsonify({"error": "Due date must be in the future."}), 400
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    bill.biller_name = data.get('biller_name', bill.biller_name)
    bill.due_date = due_date
    bill.amount = amount
    db.session.commit()
    return jsonify({"message": "Bill updated successfully"})

@bp.route('', methods=['GET'])
@jwt_required()
@swag_from({
    "tags": ["Bills"],
    "summary": "Get all bills",
    "description": "Retrieve all scheduled bills for the authenticated user.",
    "security": [{"JWT": []}],
    "responses": {
        "200": {
            "description": "A list of bills",
            "schema": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "example": 1},
                        "biller_name": {"type": "string", "example": "Electric Company"},
                        "due_date": {"type": "string", "format": "date", "example": "2023-12-31"},
                        "amount": {"type": "number", "format": "float", "example": 150.75}
                    }
                }
            }
        },
        "401": {"description": "Unauthorized"}
    }
})
def get_bills():
    user_id = get_jwt_identity()
    bills = Bill.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "id": bill.id,
        "biller_name": bill.biller_name,
        "due_date": bill.due_date,
        "amount": float(bill.amount)
    } for bill in bills])

@bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@swag_from({
    "tags": ["Bills"],
    "summary": "Delete bill by ID",
    "description": "Cancel a scheduled bill payment by its ID for the authenticated user.",
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "The bill ID"
        }
    ],
    "security": [{"JWT": []}],
    "responses": {
        "200": {
            "description": "Bill canceled successfully"
        },
        "404": {
            "description": "Bill not found"
        }
    }
})
def delete_bill(id):
    user_id = get_jwt_identity()
    bill = Bill.query.filter_by(id=id, user_id=user_id).first()
    if not bill:
        return jsonify({"error": "Bill not found"}), 404

    db.session.delete(bill)
    db.session.commit()
    return jsonify({"message": "Bill canceled successfully"})
