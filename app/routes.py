from flask import render_template, request, redirect, url_for, flash, send_file
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from app.models import User, Item, Order, Purchase, Customer, Supplier, Warehouse, InventoryBatch, StockAlert
from app.inventory_utils import (
    check_and_create_stock_alerts, get_warehouse_stock, transfer_stock,
    get_low_stock_items, get_overstock_items, get_active_stock_alerts, resolve_stock_alert
)
from app.inventory_forms import (
    WarehouseForm, EditWarehouseForm, AdvancedItemForm, EditAdvancedItemForm,
    InventoryBatchForm, EditBatchForm, StockTransferForm
)
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
    # Optional section selector from query string to show modules for a section
    from flask import request
    selected_section = request.args.get('section')

    # If requested via AJAX (or partial param), return only the dashboard content fragment.
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.args.get('partial') == '1'
    context = dict(total_items=total_items, total_orders=total_orders,
                   total_purchases=total_purchases, total_stock_value=total_stock_value,
                   selected_section=selected_section)

    if is_ajax:
        return render_template('_dashboard_content.html', **context)

    return render_template('dashboard.html', **context)

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

# ---------------- Edit Customer ----------------
@app.route('/edit_customer/<int:customer_id>', methods=['POST'])
@login_required
@roles_required('Admin', 'Manager', 'Staff')
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    customer.name = request.form.get('name')
    customer.phone = request.form.get('phone')
    customer.email = request.form.get('email')
    customer.address = request.form.get('address')
    customer.gst_number = request.form.get('gst_number')

    if not customer.name:
        flash('Customer name is required.', 'error')
        return redirect(url_for('customers'))

    db.session.commit()
    flash(f'Customer "{customer.name}" updated successfully!', 'success')
    return redirect(url_for('customers'))


# ---------------- Delete Customer ----------------
@app.route('/delete_customer/<int:customer_id>', methods=['POST'])
@login_required
@roles_required('Admin', 'Manager', 'Staff')
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    flash(f'Customer "{customer.name}" deleted successfully.', 'success')
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
        reorder_point = request.form.get('reorder_point', 10)
        max_stock = request.form.get('max_stock', 100)

        if name and quantity:
            try:
                quantity_int = int(quantity)
                price_decimal = Decimal(price or 0)
                reorder_point_int = int(reorder_point or 10)
                max_stock_int = int(max_stock or 100)
                
                if quantity_int < 0:
                    flash('Quantity cannot be negative.', 'error')
                elif reorder_point_int < 0 or max_stock_int < 0:
                    flash('Reorder point and max stock cannot be negative.', 'error')
                else:
                    item = Item(
                        name=name, 
                        quantity=quantity_int, 
                        price=price_decimal, 
                        description=description,
                        reorder_point=reorder_point_int,
                        max_stock=max_stock_int
                    )
                    db.session.add(item)
                    db.session.commit()
                    
                    # Check and create alerts
                    check_and_create_stock_alerts(item.id)
                    
                    flash('Item added successfully!', 'success')
            except ValueError:
                flash('Invalid quantity, price, or stock values. Please enter numbers.', 'error')
        else:
            flash('Please provide item name and quantity.', 'error')

    items = Item.query.all()
    low_stock_items = get_low_stock_items()
    overstock_items = get_overstock_items()
    active_alerts = get_active_stock_alerts()
    
    return render_template('inventory.html', items=items, low_stock_items=low_stock_items, 
                         overstock_items=overstock_items, active_alerts=active_alerts)

# ---------------- Edit Inventory Item ----------------
@app.route('/edit_item/<int:item_id>', methods=['POST'])
@login_required
@roles_required('Admin', 'Manager', 'Staff')
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)

    name = request.form.get('name')
    quantity = request.form.get('quantity')
    price = request.form.get('price')
    description = request.form.get('description')
    reorder_point = request.form.get('reorder_point')
    max_stock = request.form.get('max_stock')

    # Validate fields
    if not name or not quantity or not price:
        flash('Name, Quantity, and Price are required fields.', 'error')
        return redirect(url_for('inventory'))

    try:
        item.name = name
        item.quantity = int(quantity)
        item.price = float(price)
        item.description = description
        item.reorder_point = int(reorder_point or 10)
        item.max_stock = int(max_stock or 100)
        item.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Check and update alerts
        check_and_create_stock_alerts(item.id)
        
        flash(f'Item "{item.name}" updated successfully!', 'success')
    except ValueError:
        flash('Invalid quantity, price, or stock values format.', 'error')

    return redirect(url_for('inventory'))


# ----- Delete inventory Item -----
@app.route('/inventory/delete/<int:item_id>', methods=['POST'])
@login_required
@roles_required('Admin', 'Manager')
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    try:
        db.session.delete(item)
        db.session.commit()
        flash('Item deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting item: {str(e)}', 'danger')
    return redirect(url_for('inventory'))

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

        if not item_id or not order_quantity:
            flash('Please select an item and enter a quantity.', 'error')
            return redirect(url_for('sales'))

        try:
            item = Item.query.get_or_404(int(item_id))
            quantity_int = int(order_quantity)

            if quantity_int <= 0:
                flash('Quantity must be greater than zero.', 'error')
                return redirect(url_for('sales'))

            if quantity_int > item.quantity:
                flash(f'Not enough stock for {item.name}. Only {item.quantity} left.', 'error')
                return redirect(url_for('sales'))

            # Create order
            order = Order(item_id=item.id, quantity=quantity_int)

            # Assign customer if selected
            if customer_id:
                try:
                    cust = Customer.query.get(int(customer_id))
                    if cust:
                        order.customer_id = cust.id
                except Exception:
                    flash('Invalid customer selected.', 'error')

            db.session.add(order)
            item.quantity -= quantity_int
            db.session.commit()

            flash(f'Order created successfully for {quantity_int} x {item.name}!', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating order: {str(e)}', 'danger')

    orders = Order.query.order_by(Order.order_date.desc()).all()
    return render_template('sales.html', items=items, customers=customers, orders=orders)

# ---------------- View Order ----------------
@app.route('/sales/view/<int:order_id>')
@login_required
@roles_required('Admin', 'Manager', 'Staff')
def view_order(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('view_order.html', order=order)

# ---------------- Cancel Order ----------------
@app.route('/sales/cancel/<int:order_id>', methods=['POST'])
@login_required
@roles_required('Admin', 'Manager')
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    item = Item.query.get(order.item_id)

    try:
        if item:
            item.quantity += order.quantity
        db.session.delete(order)
        db.session.commit()
        flash(f'Order #{order.id} cancelled successfully. Stock restored.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error cancelling order: {str(e)}', 'danger')

    return redirect(url_for('sales'))

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


# ==================== ADVANCED INVENTORY MANAGEMENT ROUTES ====================

# --------- Warehouse Management ---------
@app.route('/warehouses', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Manager')
def warehouses():
    """List and manage warehouses"""
    if request.method == 'POST':
        form = WarehouseForm()
        if form.validate_on_submit():
            try:
                warehouse = Warehouse(
                    name=form.name.data,
                    location=form.location.data,
                    manager_name=form.manager_name.data or None,
                    phone=form.phone.data or None
                )
                db.session.add(warehouse)
                db.session.commit()
                flash(f'Warehouse "{warehouse.name}" added successfully!', 'success')
                return redirect(url_for('warehouses'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding warehouse: {str(e)}', 'error')

    form = WarehouseForm()
    warehouses_list = Warehouse.query.all()
    return render_template('warehouses.html', form=form, warehouses=warehouses_list)

@app.route('/warehouse/<int:warehouse_id>/edit', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Manager')
def edit_warehouse(warehouse_id):
    """Edit warehouse details"""
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    
    if request.method == 'POST':
        form = EditWarehouseForm()
        if form.validate_on_submit():
            try:
                warehouse.name = form.name.data
                warehouse.location = form.location.data
                warehouse.manager_name = form.manager_name.data or None
                warehouse.phone = form.phone.data or None
                db.session.commit()
                flash(f'Warehouse "{warehouse.name}" updated successfully!', 'success')
                return redirect(url_for('warehouses'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating warehouse: {str(e)}', 'error')
    else:
        form = EditWarehouseForm()
        form.name.data = warehouse.name
        form.location.data = warehouse.location
        form.manager_name.data = warehouse.manager_name
        form.phone.data = warehouse.phone
    
    return render_template('edit_warehouse.html', form=form, warehouse=warehouse)

@app.route('/warehouse/<int:warehouse_id>/delete', methods=['POST'])
@login_required
@roles_required('Admin')
def delete_warehouse(warehouse_id):
    """Delete a warehouse"""
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    
    # Check if warehouse has active batches
    active_batches = InventoryBatch.query.filter_by(warehouse_id=warehouse_id, is_active=True).count()
    if active_batches > 0:
        flash(f'Cannot delete warehouse with {active_batches} active stock batches.', 'error')
        return redirect(url_for('warehouses'))
    
    try:
        db.session.delete(warehouse)
        db.session.commit()
        flash(f'Warehouse "{warehouse.name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting warehouse: {str(e)}', 'error')
    
    return redirect(url_for('warehouses'))

@app.route('/warehouse/<int:warehouse_id>/stock', methods=['GET'])
@login_required
@roles_required('Admin', 'Manager', 'Staff')
def warehouse_stock(warehouse_id):
    """View stock in a specific warehouse"""
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    batches = InventoryBatch.query.filter_by(warehouse_id=warehouse_id).all()
    
    # Group by item
    items_stock = {}
    for batch in batches:
        if batch.item_id not in items_stock:
            items_stock[batch.item_id] = {
                'item': batch.item,
                'active_qty': 0,
                'expired_qty': 0,
                'batches': []
            }
        
        if batch.is_expired():
            items_stock[batch.item_id]['expired_qty'] += batch.quantity
        else:
            items_stock[batch.item_id]['active_qty'] += batch.quantity
        
        items_stock[batch.item_id]['batches'].append(batch)
    
    return render_template('warehouse_stock.html', warehouse=warehouse, items_stock=items_stock)

# --------- Inventory Batch Management ---------
@app.route('/batches', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Manager')
def batches():
    """List and add inventory batches"""
    form = InventoryBatchForm()
    form.item_id.choices = [(item.id, item.name) for item in Item.query.all()]
    form.warehouse_id.choices = [(w.id, w.name) for w in Warehouse.query.filter_by(is_active=True).all()]
    form.supplier_id.choices = [(0, 'None')] + [(s.id, s.name) for s in Supplier.query.all()]
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            batch = InventoryBatch(
                item_id=form.item_id.data,
                warehouse_id=form.warehouse_id.data,
                batch_number=form.batch_number.data,
                serial_number=form.serial_number.data or None,
                quantity=form.quantity.data,
                supplier_id=form.supplier_id.data if form.supplier_id.data != 0 else None,
                notes=form.notes.data or None
            )
            
            if form.expiry_date.data:
                try:
                    batch.expiry_date = datetime.strptime(form.expiry_date.data, '%Y-%m-%d')
                except ValueError:
                    flash('Invalid expiry date format. Use YYYY-MM-DD.', 'error')
                    form.supplier_id.choices = [(0, 'None')] + [(s.id, s.name) for s in Supplier.query.all()]
                    return render_template('batches.html', form=form)
            
            db.session.add(batch)
            
            # Update item quantity
            item = Item.query.get(form.item_id.data)
            item.quantity += form.quantity.data
            
            db.session.commit()
            
            # Check and create alerts
            check_and_create_stock_alerts(item.id)
            
            flash(f'Batch "{batch.batch_number}" added successfully! Item stock updated.', 'success')
            return redirect(url_for('batches'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding batch: {str(e)}', 'error')
    
    batches_list = InventoryBatch.query.order_by(InventoryBatch.received_date.desc()).all()
    return render_template('batches.html', form=form, batches=batches_list)

@app.route('/batch/<int:batch_id>/edit', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Manager')
def edit_batch(batch_id):
    """Edit batch details"""
    batch = InventoryBatch.query.get_or_404(batch_id)
    
    if request.method == 'POST':
        form = EditBatchForm()
        if form.validate_on_submit():
            try:
                # Calculate quantity difference
                old_qty = batch.quantity
                new_qty = form.quantity.data
                qty_diff = new_qty - old_qty
                
                batch.batch_number = form.batch_number.data
                batch.serial_number = form.serial_number.data or None
                batch.quantity = new_qty
                batch.notes = form.notes.data or None
                
                if form.expiry_date.data:
                    try:
                        batch.expiry_date = datetime.strptime(form.expiry_date.data, '%Y-%m-%d')
                    except ValueError:
                        flash('Invalid expiry date format. Use YYYY-MM-DD.', 'error')
                        return redirect(url_for('edit_batch', batch_id=batch_id))
                
                # Update item quantity
                batch.item.quantity += qty_diff
                
                db.session.commit()
                
                # Check and update alerts
                check_and_create_stock_alerts(batch.item_id)
                
                flash(f'Batch "{batch.batch_number}" updated successfully!', 'success')
                return redirect(url_for('batches'))
            except ValueError as e:
                flash(f'Invalid input: {str(e)}', 'error')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating batch: {str(e)}', 'error')
    else:
        form = EditBatchForm()
        form.batch_number.data = batch.batch_number
        form.serial_number.data = batch.serial_number
        form.quantity.data = batch.quantity
        if batch.expiry_date:
            form.expiry_date.data = batch.expiry_date.strftime('%Y-%m-%d')
        form.notes.data = batch.notes
    
    return render_template('edit_batch.html', form=form, batch=batch)

@app.route('/batch/<int:batch_id>/delete', methods=['POST'])
@login_required
@roles_required('Admin', 'Manager')
def delete_batch(batch_id):
    """Delete a batch and adjust item quantity"""
    batch = InventoryBatch.query.get_or_404(batch_id)
    item = batch.item
    
    try:
        # Reduce item quantity
        item.quantity -= batch.quantity
        if item.quantity < 0:
            item.quantity = 0
        
        db.session.delete(batch)
        db.session.commit()
        
        # Check and update alerts
        check_and_create_stock_alerts(item.id)
        
        flash(f'Batch "{batch.batch_number}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting batch: {str(e)}', 'error')
    
    return redirect(url_for('batches'))

# --------- Stock Transfer Between Warehouses ---------
@app.route('/stock/transfer', methods=['GET', 'POST'])
@login_required
@roles_required('Admin', 'Manager')
def transfer_stock_between_warehouses():
    """Transfer stock from one warehouse to another"""
    form = StockTransferForm()
    form.item_id.choices = [(item.id, item.name) for item in Item.query.all()]
    form.from_warehouse.choices = [(w.id, w.name) for w in Warehouse.query.filter_by(is_active=True).all()]
    form.to_warehouse.choices = [(w.id, w.name) for w in Warehouse.query.filter_by(is_active=True).all()]
    
    if request.method == 'POST' and form.validate_on_submit():
        if form.from_warehouse.data == form.to_warehouse.data:
            flash('Source and destination warehouses must be different.', 'error')
        else:
            result = transfer_stock(
                form.item_id.data,
                form.from_warehouse.data,
                form.to_warehouse.data,
                form.quantity.data,
                form.batch_number.data or None
            )
            
            if result['success']:
                flash(result['message'], 'success')
                return redirect(url_for('batches'))
            else:
                flash(result['message'], 'error')
    
    transfers = []
    return render_template('stock_transfer.html', form=form, transfers=transfers)

# --------- Stock Alerts ---------
@app.route('/stock/alerts', methods=['GET'])
@login_required
@roles_required('Admin', 'Manager')
def stock_alerts():
    """View all active stock alerts"""
    alerts = get_active_stock_alerts()
    low_stock_items = get_low_stock_items()
    overstock_items = get_overstock_items()
    
    return render_template('stock_alerts.html', alerts=alerts, low_stock_items=low_stock_items, 
                          overstock_items=overstock_items)

@app.route('/stock/alert/<int:alert_id>/resolve', methods=['POST'])
@login_required
@roles_required('Admin', 'Manager')
def resolve_alert(alert_id):
    """Mark a stock alert as resolved"""
    if resolve_stock_alert(alert_id):
        flash('Stock alert resolved successfully!', 'success')
    else:
        flash('Error resolving alert.', 'error')
    
    return redirect(url_for('stock_alerts'))
