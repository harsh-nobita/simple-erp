from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from enum import Enum
from decimal import Decimal

# ----------------- User Roles Enum -----------------
class UserRole(Enum):
    ADMIN = 'Admin'
    MANAGER = 'Manager'
    STAFF = 'Staff'

# ----------------- User Model -----------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default=UserRole.STAFF.value)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == UserRole.ADMIN.value

    def is_manager(self):
        return self.role == UserRole.MANAGER.value

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

# ----------------- Customer Model -----------------
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(15))
    email = db.Column(db.String(120))
    address = db.Column(db.String(250))
    gst_number = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship: One customer -> many orders
    orders = db.relationship('Order', backref='customer', cascade="all, delete-orphan", lazy='select')

    def __repr__(self):
        return f'<Customer {self.name}>'

# ----------------- Supplier Model -----------------
class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(15))
    email = db.Column(db.String(120))
    address = db.Column(db.String(250))
    gst_number = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship: One supplier -> many purchases
    purchases = db.relationship('Purchase', backref='supplier', cascade="all, delete-orphan", lazy='select')

    def __repr__(self):
        return f'<Supplier {self.name}>'

# ----------------- Item Model -----------------
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    price = db.Column(db.Numeric(10, 2), default=0.00)
    description = db.Column(db.String(200))

    # Relationships
    orders = db.relationship('Order', backref='item', cascade="all, delete-orphan", lazy='select')
    purchases = db.relationship('Purchase', backref='item', cascade="all, delete-orphan", lazy='select')

    def total_value(self):
        return self.quantity * self.price

    def __repr__(self):
        return f'<Item {self.name}: {self.quantity} @ ₹{self.price}>'

# ----------------- Order Model -----------------
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    invoiced = db.Column(db.Boolean, default=False)

    def total_amount(self):
        return float(self.quantity * self.item.price) if self.item else 0.0

    def __repr__(self):
        return f'<Order {self.id} for {self.quantity} of {self.item.name if self.item else "Unknown"}>'

# ----------------- Purchase Model -----------------
class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)

    def total_amount(self):
        return float(self.quantity * self.item.price) if self.item else 0.0

    def __repr__(self):
        return f'<Purchase {self.id} for {self.quantity} of {self.item.name if self.item else "Unknown"}>'
