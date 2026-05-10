from decimal import Decimal
from datetime import date
from app import db


class Billing(db.Model):
    __tablename__ = "billings"
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(128), nullable=False)
    customer = db.Column(db.String(128))
    amount = db.Column(db.Numeric(12, 2), default=0.00)
    tax_id = db.Column(db.Integer, db.ForeignKey("taxes.id"), nullable=True)
    date_issued = db.Column(db.Date, default=date.today)
    paid = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Billing {self.reference} {self.amount}>"


class Tax(db.Model):
    __tablename__ = "taxes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    rate = db.Column(db.Numeric(5, 2), default=0.00)  # percentage

    billings = db.relationship("Billing", backref="tax", lazy=True)

    def __repr__(self):
        return f"<Tax {self.name} {self.rate}%>"


class Expense(db.Model):
    __tablename__ = "expenses"
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(256))
    amount = db.Column(db.Numeric(12, 2), default=0.00)
    date = db.Column(db.Date, default=date.today)
    category = db.Column(db.String(64))

    def __repr__(self):
        return f"<Expense {self.description} {self.amount}>"


class AccountSummary(db.Model):
    __tablename__ = "account_summaries"
    id = db.Column(db.Integer, primary_key=True)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    total_billed = db.Column(db.Numeric(12, 2), default=0.00)
    total_expenses = db.Column(db.Numeric(12, 2), default=0.00)
    net = db.Column(db.Numeric(12, 2), default=0.00)

    def __repr__(self):
        return f"<AccountSummary {self.period_start} - {self.period_end}>"
