from functools import wraps
from flask import session, redirect, url_for


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated


def calculate_order_total(order_items):
    # order_items: list of dicts with 'quantity' and 'price'
    return sum(int(item.get("quantity", 0)) * float(item.get("price", 0)) for item in order_items)
