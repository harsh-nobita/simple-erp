from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField, DateField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Optional
from wtforms import ValidationError


class EmployeeForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    position = StringField("Position", validators=[Optional()])
    department = StringField("Department", validators=[Optional()])
    date_hired = DateField("Date Hired", validators=[Optional()], format="%Y-%m-%d")
    salary = DecimalField("Salary", validators=[Optional()], places=2)
    submit = SubmitField("Save")


class AttendanceForm(FlaskForm):
    employee_id = SelectField("Employee", coerce=int, validators=[DataRequired()])
    date = DateField("Date", validators=[DataRequired()], format="%Y-%m-%d")
    status = SelectField("Status", choices=[("present", "Present"), ("absent", "Absent"), ("leave", "On Leave")])
    submit = SubmitField("Record")


class PayrollForm(FlaskForm):
    employee_id = SelectField("Employee", coerce=int, validators=[DataRequired()])
    period_start = DateField("Period Start", validators=[DataRequired()], format="%Y-%m-%d")
    period_end = DateField("Period End", validators=[DataRequired()], format="%Y-%m-%d")
    gross_pay = DecimalField("Gross Pay", validators=[DataRequired()], places=2)
    taxes = DecimalField("Taxes", validators=[Optional()], places=2)
    submit = SubmitField("Process")

    def validate(self):
        rv = super().validate()
        if not rv:
            return False
        if self.period_start.data and self.period_end.data:
            if self.period_end.data < self.period_start.data:
                self.period_end.errors.append("Period end date must be the same or after period start date.")
                return False
        return True


class LeaveForm(FlaskForm):
    employee_id = SelectField("Employee", coerce=int, validators=[DataRequired()])
    start_date = DateField("Start Date", validators=[DataRequired()], format="%Y-%m-%d")
    end_date = DateField("End Date", validators=[DataRequired()], format="%Y-%m-%d")
    leave_type = StringField("Type", validators=[Optional()])
    reason = TextAreaField("Reason", validators=[Optional()])
    submit = SubmitField("Request")

    def validate(self):
        rv = super().validate()
        if not rv:
            return False
        if self.start_date.data and self.end_date.data:
            if self.end_date.data < self.start_date.data:
                self.end_date.errors.append("End date must be the same or after start date.")
                return False
        return True
