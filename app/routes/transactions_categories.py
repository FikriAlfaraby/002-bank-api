from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from flasgger import swag_from
from app.models import TransactionCategory

bp = Blueprint('transactions_categories', __name__, url_prefix='/transactions/categories')

@bp.route('', methods=['GET'])
@jwt_required()
@swag_from({
    "tags": ["Transactions Categories"],
    "summary": "Get transaction categories for budgeting",
    "description": "Retrieve a list of transaction categories that can be used for budgeting purposes.",
    "security": [{"JWT": []}],
    "responses": {
        "200": {
            "description": "A list of transaction categories",
            "schema": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "example": 1},
                        "name": {"type": "string", "example": "Groceries"}
                    }
                }
            }
        },
        "401": {"description": "Unauthorized"}
    }
})
def get_transaction_categories():
    categories = TransactionCategory.query.all()

    return jsonify([{
        "id": category.id,
        "name": category.name
    } for category in categories])
