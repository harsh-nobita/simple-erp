from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from app.models import User, Item, Order, Purchase
from datetime import datetime
from decimal import Decimal  # For precise currency math

# Dashboard route (protected by login)
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    # Simple dashboard showing user and summary
    total_items = Item.query.count()
    total_orders = Order.query.count()
    total_purchases = Purchase.query.count()
    total_stock_value = sum(item.total_value() for item in Item.query.all())  # New: Total stock value
    return render_template('dashboard.html', total_items=total_items, total_orders=total_orders, total_purchases=total_purchases, total_stock_value=total_stock_value)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Inventory route (add/view items, now with price)
@app.route('/inventory', methods=['GET', 'POST'])
@login_required
def inventory():
    if request.method == 'POST':
        name = request.form.get('name')
        quantity = request.form.get('quantity')
        price = request.form.get('price', 0)
        description = request.form.get('description', '')  # Optional
        
        if name and quantity:
            try:
                quantity_int = int(quantity)
                price_decimal = Decimal(price or 0)
                if quantity_int < 0:
                    flash('Quantity cannot be negative.', 'error')
                else:
                    item = Item(name=name, quantity=quantity_int, price=price_decimal, description=description)
                    db.session.add(item)
                    db.session.commit()
                    flash('Item added successfully!', 'success')
            except ValueError:
                flash('Invalid quantity or price. Please enter numbers.', 'error')
        else:
            flash('Please provide item name and quantity.', 'error')
    
    # Fetch all items
    items = Item.query.all()
    return render_template('inventory.html', items=items)

# Sales route (create/view orders, deduct from inventory, calculate total)
@app.route('/sales', methods=['GET', 'POST'])
@login_required
def sales():
    items = Item.query.all()  # All available items for dropdown
    
    if request.method == 'POST':
        item_id = request.form.get('item_id')
        order_quantity = request.form.get('quantity')
        
        if item_id and order_quantity:
            try:
                item = Item.query.get_or_404(int(item_id))
                order_quantity_int = int(order_quantity)
                
                if order_quantity_int <= 0:
                    flash('Order quantity must be positive.', 'error')
                elif order_quantity_int > item.quantity:
                    flash(f'Insufficient stock! Only {item.quantity} available for {item.name}.', 'error')
                else:
                    # Create order
                    order = Order(item_id=item.id, quantity=order_quantity_int)
                    db.session.add(order)
                    
                    # Deduct from inventory
                    item.quantity -= order_quantity_int
                    db.session.commit()
                    
                    total = order.total_amount()
                    flash(f'Order created successfully! Sold {order_quantity_int} x {item.name} for ₹{total}. Stock updated.', 'success')
            except ValueError:
                flash('Invalid quantity. Please enter a number.', 'error')
        else:
            flash('Please select an item and enter quantity.', 'error')
    
    # Fetch all orders for display
    orders = Order.query.all()
    return render_template('sales.html', items=items, orders=orders)

# Purchases route (create/view purchases, add to inventory, calculate total)
@app.route('/purchases', methods=['GET', 'POST'])
@login_required
def purchases():
    items = Item.query.all()  # All items for dropdown
    
    if request.method == 'POST':
        item_id = request.form.get('item_id')
        purchase_quantity = request.form.get('quantity')
        supplier = request.form.get('supplier', '')  # Optional
        
        if item_id and purchase_quantity:
            try:
                item = Item.query.get_or_404(int(item_id))
                purchase_quantity_int = int(purchase_quantity)
                
                if purchase_quantity_int <= 0:
                    flash('Purchase quantity must be positive.', 'error')
                else:
                    # Create purchase
                    purchase = Purchase(item_id=item.id, quantity=purchase_quantity_int, supplier=supplier)
                    db.session.add(purchase)
                    
                    # Add to inventory
                    item.quantity += purchase_quantity_int
                    db.session.commit()
                    
                    total = purchase.total_amount()
                    flash(f'Purchase recorded! Bought {purchase_quantity_int} x {item.name} for ₹{total}. Stock updated to {item.quantity}.', 'success')
            except ValueError:
                flash('Invalid quantity. Please enter a number.', 'error')
        else:
            flash('Please select an item and enter quantity.', 'error')
    
    # Fetch all purchases for display
    purchases_list = Purchase.query.all()
    return render_template('purchases.html', items=items, purchases=purchases_list)

# Reports route (new: summaries)
@app.route('/reports')
@login_required
def reports():
    # Sales summary
    sales_total = sum(order.total_amount() for order in Order.query.all())
    sales_count = Order.query.count()
    
    # Purchases summary
    purchases_total = sum(purchase.total_amount() for purchase in Purchase.query.all())
    purchases_count = Purchase.query.count()
    
    # Stock valuation
    stock_value = sum(item.total_value() for item in Item.query.all())
    low_stock_items = [item for item in Item.query.all() if item.quantity < 5]  # e.g., <5 units
    
    # Recent sales (last 5)
    recent_sales = Order.query.order_by(Order.order_date.desc()).limit(5).all()
    
    # Recent purchases (last 5)
    recent_purchases = Purchase.query.order_by(Purchase.purchase_date.desc()).limit(5).all()
    
    return render_template('reports.html', 
                          sales_total=sales_total, sales_count=sales_count,
                          purchases_total=purchases_total, purchases_count=purchases_count,
                          stock_value=stock_value, low_stock_items=low_stock_items,
                          recent_sales=recent_sales, recent_purchases=recent_purchases)

# Temporary route to create a test user (visit once, then remove)
@app.route('/register-test-user')
def register_test_user():
    if User.query.filter_by(username='testuser').first():
        return 'Test user already exists. Username: testuser, Password: testpassword'
    
    user = User(username='testuser')
    user.set_password('testpassword')
    db.session.add(user)
    db.session.commit()
    return 'Test user created! Username: testuser, Password: testpassword. Visit /login now.'