from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from app import db
from app.hrm import bp
from app.hrm.models import Employee, Attendance, Payroll, Leave
from app.hrm.forms import EmployeeForm, AttendanceForm, PayrollForm, LeaveForm


@bp.route("/employees")
@login_required
def employees():
    employees = Employee.query.order_by(Employee.name).all()
    return render_template("employees.html", employees=employees)


@bp.route("/employees/new", methods=["GET", "POST"])
@login_required
def new_employee():
    form = EmployeeForm()
    if form.validate_on_submit():
        e = Employee(
            name=form.name.data,
            email=form.email.data,
            position=form.position.data,
            department=form.department.data,
            date_hired=form.date_hired.data,
            salary=form.salary.data or 0,
        )
        db.session.add(e)
        db.session.commit()
        flash("Employee created.")
        return redirect(url_for("hrm.employees"))
    return render_template("employee_form.html", form=form)


@bp.route("/attendance", methods=["GET", "POST"])
@login_required
def attendance():
    form = AttendanceForm()
    # Populate employee choices
    form.employee_id.choices = [(e.id, e.name) for e in Employee.query.order_by(Employee.name).all()]
    if form.validate_on_submit():
        a = Attendance(
            employee_id=form.employee_id.data,
            date=form.date.data,
            status=form.status.data,
            check_in=None,
            check_out=None,
        )
        db.session.add(a)
        db.session.commit()
        flash("Attendance recorded.")
        return redirect(url_for("hrm.attendance"))

    records = Attendance.query.order_by(Attendance.date.desc()).limit(100).all()
    return render_template("attendance.html", records=records, form=form)


@bp.route("/payroll", methods=["GET", "POST"])
@login_required
def payroll():
    form = PayrollForm()
    form.employee_id.choices = [(e.id, e.name) for e in Employee.query.order_by(Employee.name).all()]
    if form.validate_on_submit():
        gross = form.gross_pay.data or 0
        taxes = form.taxes.data or 0
        net = gross - taxes
        p = Payroll(
            employee_id=form.employee_id.data,
            period_start=form.period_start.data,
            period_end=form.period_end.data,
            gross_pay=gross,
            taxes=taxes,
            net_pay=net,
        )
        db.session.add(p)
        db.session.commit()
        flash("Payroll processed.")
        return redirect(url_for("hrm.payroll"))

    payrolls = Payroll.query.order_by(Payroll.period_start.desc()).limit(100).all()
    return render_template("payroll.html", payrolls=payrolls, form=form)


@bp.route("/leaves", methods=["GET", "POST"])
@login_required
def leaves():
    form = LeaveForm()
    form.employee_id.choices = [(e.id, e.name) for e in Employee.query.order_by(Employee.name).all()]
    if form.validate_on_submit():
        l = Leave(
            employee_id=form.employee_id.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            leave_type=form.leave_type.data,
            reason=form.reason.data,
            status="pending",
        )
        db.session.add(l)
        db.session.commit()
        flash("Leave request submitted.")
        return redirect(url_for("hrm.leaves"))

    leaves = Leave.query.order_by(Leave.start_date.desc()).limit(100).all()
    return render_template("leave.html", leaves=leaves, form=form)
