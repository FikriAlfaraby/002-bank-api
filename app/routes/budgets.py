from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
from app import db
from app.models import Budget, TransactionCategory

bp = Blueprint('budgets', __name__, url_prefix='/budgets')

from datetime import datetime

@bp.route('', methods=['POST'])
@jwt_required()
@swag_from({
    "tags": ["Budgets"],
    "summary": "Create a new budget",
    "description": "Create a new budget for a specific category with allocated amount and date range.",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "example": "Groceries"},
                    "amount": {"type": "number", "format": "decimal", "example": 500.00},
                    "start_date": {"type": "string", "format": "date", "example": "2024-01-01"},
                    "end_date": {"type": "string", "format": "date", "example": "2024-01-31"}
                },
                "required": ["name", "amount", "start_date", "end_date"]
            }
        }
    ],
    "security": [{"JWT": []}],
    "responses": {
        "201": {"description": "Budget created successfully"},
        "400": {"description": "Invalid input"}
    }
})
def create_budget():
    user_id = get_jwt_identity()
    data = request.json

    amount = data['amount']
    if amount <= 0:
        return jsonify({"error": "Invalid amount. Amount must be greater than zero."}), 400

    start_date = data['start_date']
    end_date = data['end_date']
    
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        
        if start_date_obj < datetime.now():
            return jsonify({"error": "Start date must be in the future."}), 400
        if start_date_obj > end_date_obj:
            return jsonify({"error": "Start date cannot be after end date."}), 400
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    category = TransactionCategory.query.filter_by(name=data['name']).first()
    if not category:
        category = TransactionCategory(name=data['name'])
        db.session.add(category)
        db.session.commit()

    budget = Budget(
        user_id=user_id,
        name=category.name,
        amount=amount,
        start_date=start_date,
        end_date=end_date
    )
    db.session.add(budget)
    db.session.commit()
    
    return jsonify({"message": "Budget created successfully"}), 201

@bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@swag_from({
    "tags": ["Budgets"],
    "summary": "Update an existing budget",
    "description": "Update the details of a specific budget by its ID.",
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "The budget ID"
        },
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "example": "Groceries"},
                    "amount": {"type": "number", "format": "decimal", "example": 550.00},
                    "start_date": {"type": "string", "format": "date", "example": "2024-01-01"},
                    "end_date": {"type": "string", "format": "date", "example": "2024-01-31"}
                }
            }
        }
    ],
    "security": [{"JWT": []}],
    "responses": {
        "200": {"description": "Budget updated successfully"},
        "404": {"description": "Budget not found"},
        "400": {"description": "Invalid input"}
    }
})
def update_budget(id):
    user_id = get_jwt_identity()
    budget = Budget.query.filter_by(id=id, user_id=user_id).first()
    if not budget:
        return jsonify({"error": "Budget not found"}), 404

    data = request.json

    amount = data.get('amount', budget.amount)
    if amount <= 0:
        return jsonify({"error": "Invalid amount. Amount must be greater than zero."}), 400

    start_date = data.get('start_date', budget.start_date)
    end_date = data.get('end_date', budget.end_date)
    
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        
        if start_date_obj < datetime.now():
            return jsonify({"error": "Start date must be in the future."}), 400
        if start_date_obj > end_date_obj:
            return jsonify({"error": "Start date cannot be after end date."}), 400
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    if 'name' in data:
        category = TransactionCategory.query.filter_by(name=data['name']).first()
        if not category:
            category = TransactionCategory(name=data['name'])
            db.session.add(category)
            db.session.commit()

    budget.name = data.get('name', budget.name)
    budget.amount = amount
    budget.start_date = start_date
    budget.end_date = end_date
    db.session.commit()
    return jsonify({"message": "Budget updated successfully"})

@bp.route('', methods=['GET'])
@jwt_required()
@swag_from({
    "tags": ["Budgets"],
    "summary": "Get all budgets",
    "description": "Retrieve all budgets created by the authenticated user.",
    "security": [{"JWT": []}],
    "responses": {
        "200": {
            "description": "A list of budgets",
            "schema": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "example": 1},
                        "name": {"type": "string", "example": "Groceries"},
                        "amount": {"type": "number", "format": "decimal", "example": 500.00},
                        "start_date": {"type": "string", "format": "date", "example": "2024-01-01"},
                        "end_date": {"type": "string", "format": "date", "example": "2024-01-31"}
                    }
                }
            }
        },
        "401": {"description": "Unauthorized"}
    }
})
def get_budgets():
    user_id = get_jwt_identity()
    budgets = Budget.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "id": budget.id,
        "name": budget.name,
        "amount": float(budget.amount),
        "start_date": budget.start_date,
        "end_date": budget.end_date
    } for budget in budgets])
