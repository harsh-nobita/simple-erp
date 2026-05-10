from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, DecimalField, DateField
from wtforms.validators import DataRequired, Optional, Email


class LeadForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional()])
    source = StringField('Source', validators=[Optional()])
    submit = SubmitField('Create Lead')


class TicketForm(FlaskForm):
    lead_id = SelectField('Lead', coerce=int, validators=[Optional()])
    subject = StringField('Subject', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Create Ticket')


class NoteForm(FlaskForm):
    lead_id = SelectField('Lead', coerce=int, validators=[DataRequired()])
    content = TextAreaField('Note', validators=[DataRequired()])
    submit = SubmitField('Add Note')


class QuotationForm(FlaskForm):
    lead_id = SelectField('Lead', coerce=int, validators=[Optional()])
    reference = StringField('Reference', validators=[DataRequired()])
    amount = DecimalField('Amount', validators=[DataRequired()], places=2)
    submit = SubmitField('Create Quotation')


class FollowUpForm(FlaskForm):
    quotation_id = SelectField('Quotation', coerce=int, validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    followup_date = DateField('Follow-up Date', validators=[Optional()], format='%Y-%m-%d')
    submit = SubmitField('Schedule Follow-up')
