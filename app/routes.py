from flask import render_template, request, redirect, url_for, flash, send_file
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from app.models import User, Item, Order, Purchase, Customer, Supplier
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

# ---------------- Customers (List / Add) ----------------
@app.route('/customers', methods=['GET', 'POST'])
@login_required
def customers():
    # GET: show customers list and add form (if role permits)
    if request.method == 'POST':
        # Only Admin and Manager can add customers
        if current_user.role not in ('Admin', 'Manager'):
            flash('You do not have permission to add customers.', 'error')
            return redirect(url_for('customers'))

        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        gst_number = request.form.get('gst_number')

        if not name:
            flash('Customer name is required.', 'error')
            return redirect(url_for('customers'))

        customer = Customer(name=name, phone=phone, email=email, address=address, gst_number=gst_number)
        db.session.add(customer)
        db.session.commit()
        flash('Customer added successfully.', 'success')
        return redirect(url_for('customers'))

    customers_list = Customer.query.order_by(Customer.created_at.desc()).all()
    return render_template('customers.html', customers=customers_list)

# ---------------- Customer: Add (separate page) ----------------
@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Manager')
def add_customer():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        gst_number = request.form.get('gst_number')

        if not name:
            flash('Customer name is required.', 'error')
            return redirect(url_for('add_customer'))

        customer = Customer(name=name, phone=phone, email=email, address=address, gst_number=gst_number)
        db.session.add(customer)
        db.session.commit()
        flash('Customer created successfully.', 'success')
        return redirect(url_for('customers'))

    return render_template('customer_form.html', action='Add', customer=None)

# ---------------- Customer: Edit ----------------
@app.route('/customers/edit/<int:customer_id>', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Manager')
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    if request.method == 'POST':
        customer.name = request.form.get('name') or customer.name
        customer.phone = request.form.get('phone') or customer.phone
        customer.email = request.form.get('email') or customer.email
        customer.address = request.form.get('address') or customer.address
        customer.gst_number = request.form.get('gst_number') or customer.gst_number

        db.session.commit()
        flash('Customer updated successfully.', 'success')
        return redirect(url_for('customers'))

    return render_template('customer_form.html', action='Edit', customer=customer)

# ---------------- Customer: Delete ----------------
@app.route('/customers/delete/<int:customer_id>', methods=['POST'])
@login_required
@roles_required('Admin', 'Manager')
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    # Optional: prevent delete if customer has orders
    if customer.orders:
        flash('Cannot delete customer with existing orders.', 'error')
        return redirect(url_for('customers'))

    db.session.delete(customer)
    db.session.commit()
    flash('Customer deleted successfully.', 'success')
    return redirect(url_for('customers'))

# ---------------- Suppliers (List / Add) ----------------
@app.route('/suppliers', methods=['GET', 'POST'])
@login_required
def suppliers():
    # POST: add supplier (only Admin/Manager)
    if request.method == 'POST':
        if current_user.role not in ('Admin', 'Manager'):
            flash('You do not have permission to add suppliers.', 'error')
            return redirect(url_for('suppliers'))

        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        gst_number = request.form.get('gst_number')

        if not name:
            flash('Supplier name is required.', 'error')
            return redirect(url_for('suppliers'))

        supplier = Supplier(name=name, phone=phone, email=email, address=address, gst_number=gst_number)
        db.session.add(supplier)
        db.session.commit()
        flash('Supplier added successfully.', 'success')
        return redirect(url_for('suppliers'))

    suppliers_list = Supplier.query.order_by(Supplier.created_at.desc()).all()
    return render_template('suppliers.html', suppliers=suppliers_list)

# ---------------- Supplier: Add (separate page) ----------------
@app.route('/suppliers/add', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Manager')
def add_supplier():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        gst_number = request.form.get('gst_number')

        if not name:
            flash('Supplier name is required.', 'error')
            return redirect(url_for('add_supplier'))

        supplier = Supplier(name=name, phone=phone, email=email, address=address, gst_number=gst_number)
        db.session.add(supplier)
        db.session.commit()
        flash('Supplier created successfully.', 'success')
        return redirect(url_for('suppliers'))

    return render_template('supplier_form.html', action='Add', supplier=None)

# ---------------- Supplier: Edit ----------------
@app.route('/suppliers/edit/<int:supplier_id>', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Manager')
def edit_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    if request.method == 'POST':
        supplier.name = request.form.get('name') or supplier.name
        supplier.phone = request.form.get('phone') or supplier.phone
        supplier.email = request.form.get('email') or supplier.email
        supplier.address = request.form.get('address') or supplier.address
        supplier.gst_number = request.form.get('gst_number') or supplier.gst_number

        db.session.commit()
        flash('Supplier updated successfully.', 'success')
        return redirect(url_for('suppliers'))

    return render_template('supplier_form.html', action='Edit', supplier=supplier)

# ---------------- Supplier: Delete ----------------
@app.route('/suppliers/delete/<int:supplier_id>', methods=['POST'])
@login_required
@roles_required('Admin', 'Manager')
def delete_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    # Optional: prevent delete if supplier has purchases
    if supplier.purchases:
        flash('Cannot delete supplier with existing purchases.', 'error')
        return redirect(url_for('suppliers'))

    db.session.delete(supplier)
    db.session.commit()
    flash('Supplier deleted successfully.', 'success')
    return redirect(url_for('suppliers'))

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
    customers = Customer.query.order_by(Customer.name).all()

    if request.method == 'POST':
        item_id = request.form.get('item_id')
        order_quantity = request.form.get('quantity')
        customer_id = request.form.get('customer_id')

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

                    # Assign customer to order if selected
                    if customer_id and customer_id != "":
                        try:
                            cid = int(customer_id)
                            customer = Customer.query.get(cid)
                            if customer:
                                order.customer_id = customer.id
                        except ValueError:
                            flash('Invalid customer selection.', 'error')

                    db.session.add(order)
                    item.quantity -= order_quantity_int
                    db.session.commit()

                    total = order.total_amount()
                    flash(f'Order created successfully! Sold {order_quantity_int} x {item.name} for ₹{total}.', 'success')
            except ValueError:
                flash('Invalid quantity. Please enter a valid number.', 'error')
        else:
            flash('Please select an item and enter a quantity.', 'error')

    # 👇 Fetch all orders with customer relationship
    orders = Order.query.order_by(Order.order_date.desc()).all()

    return render_template('sales.html', items=items, customers=customers, orders=orders)

# ---------------- Purchases ----------------
@app.route('/purchases', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Manager')
def purchases():
    items = Item.query.all()
    suppliers = Supplier.query.all()  # To select supplier in purchase form

    if request.method == 'POST':
        item_id = request.form.get('item_id')
        purchase_quantity = request.form.get('quantity')
        supplier_id = request.form.get('supplier_id')  # optional

        if item_id and purchase_quantity:
            try:
                item = Item.query.get_or_404(int(item_id))
                purchase_quantity_int = int(purchase_quantity)

                if purchase_quantity_int <= 0:
                    flash('Purchase quantity must be positive.', 'error')
                else:
                    purchase = Purchase(item_id=item.id, quantity=purchase_quantity_int)
                    if supplier_id:
                        try:
                            sid = int(supplier_id)
                            purchase.supplier_id = sid
                        except ValueError:
                            pass

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
    return render_template('purchases.html', items=items, purchases=purchases_list, suppliers=suppliers)

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
