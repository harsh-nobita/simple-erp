from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from enum import Enum

# ----------------- User Roles Enum -----------------
class UserRole(Enum):
    ADMIN = 'Admin'
    MANAGER = 'Manager'
    STAFF = 'Staff'

# User model (inherits from UserMixin for Flask-Login support)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)  # Renamed for clarity
    role = db.Column(db.String(20), default=UserRole.STAFF.value)

    # Methods for password handling
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == UserRole.ADMIN.value

    def is_manager(self):
        return self.role == UserRole.MANAGER.value

# Item model for inventory (add price)
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    price = db.Column(db.Numeric(10, 2), default=0.00)  # New: Price per unit (e.g., 100.00)
    description = db.Column(db.String(200))  # Optional field

    # Backrefs auto-created by Order and Purchase relationships

    def total_value(self):
        return self.quantity * self.price  # Helper: Stock value

    def __repr__(self):
        return f'<Item {self.name}: {self.quantity} @ ₹{self.price}>'

# Order model for sales
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)  # Auto-set date
    invoiced = db.Column(db.Boolean, default=False)  # New field

    # One-to-many: Order -> Item (backref auto-creates Item.orders)
    item = db.relationship('Item', backref='orders', lazy='select')

    def total_amount(self):
        return self.quantity * self.item.price  # New: Order total

    def __repr__(self):
        return f'<Order {self.id} for {self.quantity} of {self.item.name}>'

# Purchase model for buying stock
class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    supplier = db.Column(db.String(100))  # Optional supplier name
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)  # Auto-set date

    # One-to-many: Purchase -> Item (backref auto-creates Item.purchases)
    item = db.relationship('Item', backref='purchases', lazy='select')

    def total_amount(self):
        return self.quantity * self.item.price  # New: Purchase total

    def __repr__(self):
        return f'<Purchase {self.id} for {self.quantity} of {self.item.name}>'