from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from app.config import Config
from flasgger import Swagger

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SWAGGER'] = {
        'title': 'Banking API',
        'uiversion': 3,
        'securityDefinitions': {
            'JWT': {
                'type': 'apiKey',
                'in': 'header',
                'name': 'Authorization',
                'description': 'Enter the JWT token with `Bearer <token>` format'
            }
        },
        'security': [
            {'JWT': []}
        ]
    }
    Swagger(app)
    
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from app.routes import users, accounts, transactions, budgets, bills, transactions_categories
    app.register_blueprint(users.bp)
    app.register_blueprint(accounts.bp)
    app.register_blueprint(transactions.bp)
    app.register_blueprint(budgets.bp)
    app.register_blueprint(bills.bp)
    app.register_blueprint(transactions_categories.bp)
    
    return app
