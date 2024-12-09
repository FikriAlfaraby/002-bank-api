from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flasgger import swag_from
from app import db
from app.models import Transaction, Account

bp = Blueprint('transactions', __name__, url_prefix='/transactions')

@bp.route('', methods=['GET'])
@jwt_required()
@swag_from({
    "tags": ["Transactions"],
    "summary": "Get all transactions",
    "description": "Retrieve all transactions for the authenticated user's accounts. Optional filters: account ID, date range.",
    "parameters": [
        {
            "name": "account_id",
            "in": "query",
            "type": "integer",
            "required": False,
            "description": "Filter by specific account ID",
            "example": 1
        },
        {
            "name": "start_date",
            "in": "query",
            "type": "string",
            "format": "date",
            "required": False,
            "description": "Filter by transactions starting from this date (YYYY-MM-DD)",
            "example": "2023-01-01"
        },
        {
            "name": "end_date",
            "in": "query",
            "type": "string",
            "format": "date",
            "required": False,
            "description": "Filter by transactions up to this date (YYYY-MM-DD)",
            "example": "2023-12-31"
        }
    ],
    "security": [{"JWT": []}],
    "responses": {
        "200": {
            "description": "A list of transactions",
            "schema": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "example": 1},
                        "amount": {"type": "number", "format": "float", "example": 100.50},
                        "type": {"type": "string", "example": "transfer"},
                        "description": {"type": "string", "example": "Payment for services"},
                        "created_at": {"type": "string", "format": "datetime", "example": "2023-12-01T10:00:00"}
                    }
                }
            }
        },
        "401": {"description": "Unauthorized"}
    }
})
def get_transactions():
    user_id = get_jwt_identity()
    account_id = request.args.get("account_id", type=int)
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    query = Transaction.query.join(Account).filter(Account.user_id == user_id)

    if account_id:
        query = query.filter(Transaction.from_account_id == account_id)

    if start_date:
        query = query.filter(Transaction.created_at >= start_date)

    if end_date:
        query = query.filter(Transaction.created_at <= end_date)

    transactions = query.all()
    return jsonify([{
        "id": transaction.id,
        "amount": float(transaction.amount),
        "type": transaction.type,
        "description": transaction.description,
        "created_at": transaction.created_at
    } for transaction in transactions])

@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
@swag_from({
    "tags": ["Transactions"],
    "summary": "Get transaction details",
    "description": "Retrieve details of a specific transaction by its ID. Authorization required for the related account owner.",
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "Transaction ID",
            "example": 1
        }
    ],
    "security": [{"JWT": []}],
    "responses": {
        "200": {
            "description": "Details of the transaction",
            "schema": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "amount": {"type": "number", "format": "float", "example": 100.50},
                    "type": {"type": "string", "example": "transfer"},
                    "description": {"type": "string", "example": "Payment for services"},
                    "created_at": {"type": "string", "format": "datetime", "example": "2023-12-01T10:00:00"}
                }
            }
        },
        "401": {"description": "Unauthorized"},
        "404": {"description": "Transaction not found"}
    }
})
def get_transaction(id):
    user_id = get_jwt_identity()
    transaction = Transaction.query.join(Account).filter(
        Transaction.id == id,
        Account.user_id == user_id
    ).first()

    if not transaction:
        return jsonify({"error": "Transaction not found"}), 404

    return jsonify({
        "id": transaction.id,
        "amount": float(transaction.amount),
        "type": transaction.type,
        "description": transaction.description,
        "created_at": transaction.created_at
    })

@bp.route('', methods=['POST'])
@jwt_required()
@swag_from({
    "tags": ["Transactions"],
    "summary": "Create a new transaction",
    "description": "Initiate a transaction from one account to another.",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "from_account_id": {"type": "integer", "example": 1},
                    "to_account_id": {"type": "integer", "example": 2},
                    "amount": {"type": "number", "format": "float", "example": 150.75},
                    "type": {"type": "string", "example": "transfer"},
                    "description": {"type": "string", "example": "Payment for services"}
                },
                "required": ["from_account_id", "to_account_id", "amount", "type"]
            }
        }
    ],
    "security": [{"JWT": []}],
    "responses": {
        "201": {"description": "Transaction successful"},
        "403": {"description": "Unauthorized transaction"},
        "404": {"description": "Recipient account not found"},
        "400": {"description": "Invalid transaction amount"}
    }
})
def create_transaction():
    user_id = get_jwt_identity()
    data = request.json

    from_account = Account.query.filter_by(id=data['from_account_id'], user_id=user_id).first()
    if not from_account:
        return jsonify({"error": "Unauthorized transaction"}), 403

    to_account = Account.query.get(data['to_account_id'])
    if not to_account:
        return jsonify({"error": "Recipient account not found"}), 404

    amount = data['amount']
    if amount <= 0:
        return jsonify({"error": "Invalid transaction amount. Amount must be greater than zero."}), 400

    if from_account.balance < amount:
        return jsonify({"error": "Insufficient funds in the source account."}), 403

    if from_account.id == to_account.id:
        return jsonify({"error": "Cannot transfer to the same account."}), 400

    transaction = Transaction(
        from_account_id=from_account.id,
        to_account_id=to_account.id,
        amount=amount,
        type=data['type'],
        description=data.get('description', "")
    )
    
    from_account.balance -= amount
    to_account.balance += amount
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({"message": "Transaction successful"}), 201

