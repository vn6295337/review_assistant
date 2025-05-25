"""
Database models for the application.
"""

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from typing import Dict, Any
import pytz

db = SQLAlchemy()

# Define the local timezone (UTC+5:30)
IST = pytz.timezone("Asia/Kolkata")

def now_ist() -> datetime:
    """Return current time in IST timezone."""
    return datetime.now(IST)

class User(db.Model):
    """User model for authentication and user management."""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_ist)

    orders = db.relationship('Order', backref='user', lazy=True)

    def __init__(self, username: str, email: str, password: str) -> None:
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.email})>"

class Product(db.Model):
    """Product model for the store."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=now_ist)

    order_items = db.relationship('OrderItem', backref='product', lazy=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock': self.stock,
            'category': self.category
        }

    def __repr__(self) -> str:
        return f"<Product {self.name} (${self.price})>"

class Order(db.Model):
    """Order model for tracking purchases."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, shipped, delivered, cancelled
    total_amount = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=now_ist)

    items = db.relationship('OrderItem', backref='order', lazy=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'status': self.status,
            'total_amount': self.total_amount,
            'created_at': self.created_at.isoformat(),
            'items': [item.to_dict() for item in self.items]
        }

    def __repr__(self) -> str:
        return f"<Order {self.id} Status: {self.status} Total: {self.total_amount}>"

class OrderItem(db.Model):
    """Order item for linking products to orders."""

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_time = db.Column(db.Float, nullable=False)  # Price when ordered

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'price_at_time': self.price_at_time
        }

    def __repr__(self) -> str:
        return f"<OrderItem {self.id} Product: {self.product_id} Qty: {self.quantity}>"
