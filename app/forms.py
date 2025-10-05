from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DecimalField
from wtforms.validators import DataRequired


class ItemForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    sku = StringField("SKU", validators=[DataRequired()])
    quantity = IntegerField("Quantity")
    price = DecimalField("Price")
