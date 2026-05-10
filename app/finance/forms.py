from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField, DateField, SelectField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Optional


class BillForm(FlaskForm):
    reference = StringField("Reference", validators=[DataRequired()])
    customer = StringField("Customer", validators=[Optional()])
    amount = DecimalField("Amount", validators=[DataRequired()], places=2)
    tax_id = SelectField("Tax", coerce=int, validators=[Optional()])
    date_issued = DateField("Date Issued", validators=[Optional()], format="%Y-%m-%d")
    paid = BooleanField("Paid")
    submit = SubmitField("Save")


class ExpenseForm(FlaskForm):
    description = StringField("Description", validators=[DataRequired()])
    amount = DecimalField("Amount", validators=[DataRequired()], places=2)
    date = DateField("Date", validators=[Optional()], format="%Y-%m-%d")
    category = StringField("Category", validators=[Optional()])
    submit = SubmitField("Add")


class TaxForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    rate = DecimalField("Rate (%)", validators=[DataRequired()], places=2)
    submit = SubmitField("Save")


class AccountSummaryForm(FlaskForm):
    period_start = DateField("Period Start", validators=[DataRequired()], format="%Y-%m-%d")
    period_end = DateField("Period End", validators=[DataRequired()], format="%Y-%m-%d")
    submit = SubmitField("Generate")
