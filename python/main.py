#!/usr/bin/env python3
"""
Main entry point for the web application.
Initializes the Flask server, sets up routes, and configures the database.
"""
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from .auth import authenticate_user, create_jwt_token
from .models import db, User, Product

load_dotenv()


def create_app():
    """Factory to create and configure the Flask app."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    @app.route('/')
    def index():
        """Return the main page."""
        return jsonify({"status": "ok", "message": "Welcome to the API"})

    @app.route('/login', methods=['POST'])
    def login():
        """Authenticate user and return a JWT token."""
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid input"}), 400

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        user = authenticate_user(username, password)
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401

        token = create_jwt_token(user.id)
        return jsonify({"token": token, "user_id": user.id})

    @app.route('/products', methods=['GET'])
    def get_products():
        """Return list of all products."""
        products = Product.query.all()
        return jsonify([p.to_dict() for p in products])

    @app.route('/products/<int:product_id>', methods=['GET'])
    def get_product(product_id):
        """Return details for a specific product."""
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"error": "Product not found"}), 404
        return jsonify(product.to_dict())

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
