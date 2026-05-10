from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField, DateTimeField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Email, ValidationError
from app.models import Warehouse, Item

# ==================== Warehouse Forms ====================
class WarehouseForm(FlaskForm):
    name = StringField('Warehouse Name', validators=[DataRequired()], render_kw={"placeholder": "e.g., Main Store"})
    location = StringField('Location', validators=[DataRequired()], render_kw={"placeholder": "e.g., Delhi, Zone-A"})
    manager_name = StringField('Manager Name', validators=[Optional()], render_kw={"placeholder": "Manager name (optional)"})
    phone = StringField('Phone', validators=[Optional()], render_kw={"placeholder": "+91-XXXXXXXXXX"})
    submit = SubmitField('Add Warehouse')

class EditWarehouseForm(FlaskForm):
    name = StringField('Warehouse Name', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    manager_name = StringField('Manager Name', validators=[Optional()])
    phone = StringField('Phone', validators=[Optional()])
    submit = SubmitField('Update Warehouse')

# ==================== Advanced Item Forms ====================
class AdvancedItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired()], render_kw={"placeholder": "Enter item name"})
    quantity = IntegerField('Initial Quantity', validators=[DataRequired()], render_kw={"placeholder": "0"})
    price = DecimalField('Price per Unit (₹)', validators=[DataRequired()], places=2, render_kw={"placeholder": "0.00"})
    description = TextAreaField('Description', validators=[Optional()], rows=2, render_kw={"placeholder": "Optional description"})
    reorder_point = IntegerField('Reorder Point', default=10, validators=[DataRequired()], render_kw={"placeholder": "Alert at this quantity"})
    max_stock = IntegerField('Maximum Stock', default=100, validators=[DataRequired()], render_kw={"placeholder": "Max recommended"})
    submit = SubmitField('Add Item')

class EditAdvancedItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    price = DecimalField('Price per Unit (₹)', validators=[DataRequired()], places=2)
    description = TextAreaField('Description', validators=[Optional()])
    reorder_point = IntegerField('Reorder Point', validators=[DataRequired()])
    max_stock = IntegerField('Maximum Stock', validators=[DataRequired()])
    submit = SubmitField('Update Item')

# ==================== Inventory Batch Forms ====================
class InventoryBatchForm(FlaskForm):
    item_id = SelectField('Item', coerce=int, validators=[DataRequired()])
    warehouse_id = SelectField('Warehouse', coerce=int, validators=[DataRequired()])
    batch_number = StringField('Batch/Lot Number', validators=[DataRequired()], render_kw={"placeholder": "e.g., BATCH-2024-001"})
    serial_number = StringField('Serial Number', validators=[Optional()], render_kw={"placeholder": "Individual serial (optional)"})
    quantity = IntegerField('Quantity', validators=[DataRequired()], render_kw={"placeholder": "Number of units"})
    expiry_date = StringField('Expiry Date', validators=[Optional()], render_kw={"placeholder": "YYYY-MM-DD (optional)"})
    supplier_id = SelectField('Supplier (Optional)', coerce=int, validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()], rows=2, render_kw={"placeholder": "Additional notes"})
    submit = SubmitField('Add Batch')

class EditBatchForm(FlaskForm):
    batch_number = StringField('Batch/Lot Number', validators=[DataRequired()])
    serial_number = StringField('Serial Number', validators=[Optional()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    expiry_date = StringField('Expiry Date', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Update Batch')

# ==================== Stock Movement/Transfer Form ====================
class StockTransferForm(FlaskForm):
    item_id = SelectField('Item', coerce=int, validators=[DataRequired()])
    from_warehouse = SelectField('From Warehouse', coerce=int, validators=[DataRequired()])
    to_warehouse = SelectField('To Warehouse', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()], render_kw={"placeholder": "Units to transfer"})
    batch_number = StringField('Batch Number', validators=[Optional()], render_kw={"placeholder": "Specific batch (optional)"})
    notes = TextAreaField('Transfer Notes', validators=[Optional()], rows=2)
    submit = SubmitField('Transfer Stock')

# ==================== Stock Alert Form ====================
class ResolveStockAlertForm(FlaskForm):
    alert_id = IntegerField('Alert ID', validators=[DataRequired()])
    resolution_notes = TextAreaField('Resolution Notes', validators=[Optional()], rows=2)
    submit = SubmitField('Resolve Alert')
