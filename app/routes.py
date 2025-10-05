from flask import render_template, request, redirect, url_for, flash, send_file
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from app.models import User, Item, Order, Purchase
from datetime import datetime, date
from decimal import Decimal
from xhtml2pdf import pisa
import io
from functools import wraps

# ---------------- Role-based access decorator ----------------
def roles_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_view(*args, **kwargs):
            if current_user.role not in roles:
                flash("You do not have permission to access this page.", "error")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return decorated_view
    return wrapper

# ---------------- Dashboard ----------------
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    total_items = Item.query.count()
    total_orders = Order.query.count()
    total_purchases = Purchase.query.count()
    total_stock_value = sum(item.total_value() for item in Item.query.all())
    return render_template('dashboard.html', 
                           total_items=total_items, total_orders=total_orders, 
                           total_purchases=total_purchases, total_stock_value=total_stock_value)

# ---------------- Login with Role ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        user = User.query.filter_by(username=username).first()

        if not role:
            flash('Please select a role.', 'error')
            return redirect(url_for('login'))

        if user and user.check_password(password):
            if user.role != role:
                flash(f'Incorrect role selected. Your role is {user.role}.', 'error')
                return redirect(url_for('login'))

            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

# ---------------- Logout ----------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ---------------- Inventory ----------------
@app.route('/inventory', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Manager')
def inventory():
    if request.method == 'POST':
        name = request.form.get('name')
        quantity = request.form.get('quantity')
        price = request.form.get('price', 0)
        description = request.form.get('description', '')
        
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
    
    items = Item.query.all()
    return render_template('inventory.html', items=items)

# ---------------- Sales ----------------
@app.route('/sales', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Manager', 'Staff')
def sales():
    items = Item.query.all()
    
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
                    order = Order(item_id=item.id, quantity=order_quantity_int)
                    db.session.add(order)
                    item.quantity -= order_quantity_int
                    db.session.commit()
                    
                    total = order.total_amount()
                    flash(f'Order created successfully! Sold {order_quantity_int} x {item.name} for ₹{total}. Stock updated.', 'success')
            except ValueError:
                flash('Invalid quantity. Please enter a number.', 'error')
        else:
            flash('Please select an item and enter quantity.', 'error')
    
    orders = Order.query.all()
    return render_template('sales.html', items=items, orders=orders)

# ---------------- Purchases ----------------
@app.route('/purchases', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Manager')
def purchases():
    items = Item.query.all()
    
    if request.method == 'POST':
        item_id = request.form.get('item_id')
        purchase_quantity = request.form.get('quantity')
        supplier = request.form.get('supplier', '')
        
        if item_id and purchase_quantity:
            try:
                item = Item.query.get_or_404(int(item_id))
                purchase_quantity_int = int(purchase_quantity)
                
                if purchase_quantity_int <= 0:
                    flash('Purchase quantity must be positive.', 'error')
                else:
                    purchase = Purchase(item_id=item.id, quantity=purchase_quantity_int, supplier=supplier)
                    db.session.add(purchase)
                    item.quantity += purchase_quantity_int
                    db.session.commit()
                    
                    total = purchase.total_amount()
                    flash(f'Purchase recorded! Bought {purchase_quantity_int} x {item.name} for ₹{total}. Stock updated to {item.quantity}.', 'success')
            except ValueError:
                flash('Invalid quantity. Please enter a number.', 'error')
        else:
            flash('Please select an item and enter quantity.', 'error')
    
    purchases_list = Purchase.query.all()
    return render_template('purchases.html', items=items, purchases=purchases_list)

# ---------------- Reports ----------------
@app.route('/reports')
@login_required
@roles_required('Admin')
def reports():
    sales_total = sum(order.total_amount() for order in Order.query.all())
    sales_count = Order.query.count()
    purchases_total = sum(purchase.total_amount() for purchase in Purchase.query.all())
    purchases_count = Purchase.query.count()
    stock_value = sum(item.total_value() for item in Item.query.all())
    low_stock_items = [item for item in Item.query.all() if item.quantity < 5]
    recent_sales = Order.query.order_by(Order.order_date.desc()).limit(5).all()
    recent_purchases = Purchase.query.order_by(Purchase.purchase_date.desc()).limit(5).all()
    
    return render_template('reports.html', 
                          sales_total=sales_total, sales_count=sales_count,
                          purchases_total=purchases_total, purchases_count=purchases_count,
                          stock_value=stock_value, low_stock_items=low_stock_items,
                          recent_sales=recent_sales, recent_purchases=recent_purchases)

#---------------- About Page ----------------
@app.route('/about')
@login_required  # optional
def about():
    return render_template('about.html')

# ---------------- Temporary Test User ----------------
@app.route('/register-test-user')
def register_test_user():
    if User.query.filter_by(username='testuser').first():
        return 'Test user already exists. Username: testuser, Password: testpassword'
    
    user = User(username='testuser', role='Admin')  # Assign Admin role
    user.set_password('testpassword')
    db.session.add(user)
    db.session.commit()
    return 'Test user created! Username: testuser, Password: testpassword. Visit /login now.'

# ---------------- Invoice Module ----------------
@app.route('/invoice', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Manager')
def invoice():
    pending_orders = Order.query.filter_by(invoiced=False).all()

    if request.method == "POST":
        po_number = request.form.get("po_number")
        po_date = request.form.get("po_date")
        company_name = request.form.get("company_name")
        selected_order_ids = request.form.getlist("order_ids")

        if not po_number or not po_date or not company_name:
            flash('Please fill in all fields.', 'error')
            return redirect(url_for('invoice'))

        if not selected_order_ids:
            flash('Please select at least one order to invoice.', 'error')
            return redirect(url_for('invoice'))

        orders = Order.query.filter(Order.id.in_(selected_order_ids)).all()

        items = []
        total = 0
        for order in orders:
            item_total = order.total_amount()
            items.append({
                "name": order.item.name,
                "qty": order.quantity,
                "price": order.item.price,
                "total": item_total
            })
            total += item_total
            order.invoiced = True

        db.session.commit()

        rendered = render_template(
            'invoice.html',
            po_number=po_number,
            po_date=po_date,
            company_name=company_name,
            items=items,
            total=total
        )

        pdf = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.BytesIO(rendered.encode('utf-8')), dest=pdf)
        pdf.seek(0)

        if pisa_status.err:
            flash("Error generating PDF. Please check invoice HTML.", "error")
            return redirect(url_for('invoice'))

        return send_file(pdf, download_name=f"Invoice_{po_number}.pdf", as_attachment=True)

    return render_template('invoice_form.html', pending_orders=pending_orders, current_date=date.today())
