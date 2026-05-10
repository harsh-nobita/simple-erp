from datetime import date
from app import db


class Employee(db.Model):
    __tablename__ = "employees"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    position = db.Column(db.String(64))
    department = db.Column(db.String(64))
    date_hired = db.Column(db.Date, default=date.today)
    salary = db.Column(db.Numeric(12, 2), default=0.00)

    attendances = db.relationship("Attendance", backref="employee", lazy=True)
    payrolls = db.relationship("Payroll", backref="employee", lazy=True)
    leaves = db.relationship("Leave", backref="employee", lazy=True)

    def __repr__(self):
        return f"<Employee {self.name} ({self.id})>"


class Attendance(db.Model):
    __tablename__ = "attendances"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="present")  # present/absent/leave
    check_in = db.Column(db.Time, nullable=True)
    check_out = db.Column(db.Time, nullable=True)

    def __repr__(self):
        return f"<Attendance {self.employee_id} {self.date} {self.status}>"


class Payroll(db.Model):
    __tablename__ = "payrolls"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    gross_pay = db.Column(db.Numeric(12, 2), default=0.00)
    taxes = db.Column(db.Numeric(12, 2), default=0.00)
    net_pay = db.Column(db.Numeric(12, 2), default=0.00)

    def __repr__(self):
        return f"<Payroll {self.employee_id} {self.period_start} - {self.period_end}>"


class Leave(db.Model):
    __tablename__ = "leaves"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    leave_type = db.Column(db.String(64))
    status = db.Column(db.String(32), default="pending")  # pending/approved/rejected
    reason = db.Column(db.Text)

    def __repr__(self):
        return f"<Leave {self.employee_id} {self.start_date} to {self.end_date}>"
