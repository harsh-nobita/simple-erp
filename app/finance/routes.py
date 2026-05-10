from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.finance import bp
from app.finance.models import Billing, Tax, Expense, AccountSummary
from app.finance.forms import BillForm, ExpenseForm, TaxForm, AccountSummaryForm


@bp.route("/billing")
@login_required
def billing():
    bills = Billing.query.order_by(Billing.date_issued.desc()).limit(200).all()
    return render_template("billing.html", bills=bills)


@bp.route("/billing/add", methods=["GET", "POST"])
@login_required
def add_bill():
    # Only Admins and Managers may add bills
    if getattr(current_user, 'role', None) not in ["Admin", "Manager"]:
        abort(403)

    form = BillForm()
    form.tax_id.choices = [(0, "- None -")] + [(t.id, f"{t.name} ({t.rate}%)") for t in Tax.query.order_by(Tax.name).all()]
    if form.validate_on_submit():
        tax = form.tax_id.data if form.tax_id.data != 0 else None
        b = Billing(
            reference=form.reference.data,
            customer=form.customer.data,
            amount=form.amount.data or 0,
            tax_id=tax,
            date_issued=form.date_issued.data,
            paid=bool(form.paid.data),
        )
        db.session.add(b)
        db.session.commit()
        flash("Bill added.")
        return redirect(url_for("finance.billing"))
    return render_template("add_bill.html", form=form)


@bp.route("/taxes", methods=["GET", "POST"])
@login_required
def taxes():
    # Only Admins and Managers may manage taxes
    if getattr(current_user, 'role', None) not in ["Admin", "Manager"]:
        abort(403)

    form = TaxForm()
    if form.validate_on_submit():
        t = Tax(name=form.name.data, rate=form.rate.data or 0)
        db.session.add(t)
        db.session.commit()
        flash("Tax saved.")
        return redirect(url_for("finance.taxes"))
    taxes = Tax.query.order_by(Tax.name).all()
    return render_template("tax.html", taxes=taxes, form=form)


@bp.route("/expenses", methods=["GET", "POST"])
@login_required
def expenses():
    form = ExpenseForm()
    if form.validate_on_submit():
        e = Expense(description=form.description.data, amount=form.amount.data or 0, date=form.date.data, category=form.category.data)
        db.session.add(e)
        db.session.commit()
        flash("Expense added.")
        return redirect(url_for("finance.expenses"))
    expenses = Expense.query.order_by(Expense.date.desc()).limit(200).all()
    return render_template("expenses.html", expenses=expenses, form=form)


@bp.route("/accounts", methods=["GET", "POST"])
@login_required
def accounts_summary():
    # Only Admins and Managers may generate account summaries
    if getattr(current_user, 'role', None) not in ["Admin", "Manager"]:
        abort(403)

    form = AccountSummaryForm()
    summary = None
    if form.validate_on_submit():
        start = form.period_start.data
        end = form.period_end.data
        # aggregate simple totals
        total_billed = db.session.query(db.func.coalesce(db.func.sum(Billing.amount), 0)).filter(Billing.date_issued >= start, Billing.date_issued <= end).scalar()
        total_expenses = db.session.query(db.func.coalesce(db.func.sum(Expense.amount), 0)).filter(Expense.date >= start, Expense.date <= end).scalar()
        net = total_billed - total_expenses
        summary = {
            'period_start': start,
            'period_end': end,
            'total_billed': total_billed,
            'total_expenses': total_expenses,
            'net': net,
        }
    return render_template("accounts_summary.html", summary=summary, form=form)
