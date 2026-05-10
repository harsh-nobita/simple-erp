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

# ----------------- Warehouse Model -----------------
class Warehouse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    location = db.Column(db.String(250), nullable=False)
    manager_name = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    inventory_batches = db.relationship('InventoryBatch', backref='warehouse', cascade="all, delete-orphan", lazy='select')

    def __repr__(self):
        return f'<Warehouse {self.name} ({self.location})>'

# ----------------- Item Model -----------------
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    price = db.Column(db.Numeric(10, 2), default=0.00)
    description = db.Column(db.String(200))
    
    # Advanced Inventory Management Fields
    reorder_point = db.Column(db.Integer, default=10)  # Alert when stock drops below this
    max_stock = db.Column(db.Integer, default=100)    # Maximum recommended stock level
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    orders = db.relationship('Order', backref='item', cascade="all, delete-orphan", lazy='select')
    purchases = db.relationship('Purchase', backref='item', cascade="all, delete-orphan", lazy='select')
    batches = db.relationship('InventoryBatch', backref='item', cascade="all, delete-orphan", lazy='select')
    stock_alerts = db.relationship('StockAlert', backref='item', cascade="all, delete-orphan", lazy='select')

    def total_value(self):
        return self.quantity * self.price
    
    def is_low_stock(self):
        """Check if item is below reorder point"""
        return self.quantity < self.reorder_point
    
    def is_overstock(self):
        """Check if item exceeds max stock"""
        return self.quantity > self.max_stock

    def __repr__(self):
        return f'<Item {self.name}: {self.quantity} @ ₹{self.price}>'

# ----------------- Inventory Batch Model -----------------
class InventoryBatch(db.Model):
    __tablename__ = "inventory_batches"
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouse.id'), nullable=False)
    
    batch_number = db.Column(db.String(50), nullable=False)  # Unique batch/lot ID
    serial_number = db.Column(db.String(100))                # Individual serial number (optional)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    
    received_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime)                     # For perishable items
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'))
    
    notes = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    
    supplier = db.relationship('Supplier', backref='batches')

    def is_expired(self):
        """Check if batch has expired"""
        if self.expiry_date:
            return datetime.utcnow() > self.expiry_date
        return False

    def __repr__(self):
        return f'<InventoryBatch {self.batch_number}: {self.quantity} units>'

# ----------------- Stock Alert Model -----------------
class StockAlert(db.Model):
    __tablename__ = "stock_alerts"
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    alert_type = db.Column(db.String(20), nullable=False)  # 'low_stock', 'overstock', 'expired'
    message = db.Column(db.String(250), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<StockAlert {self.item.name}: {self.alert_type}>'

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
