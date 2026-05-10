from functools import wraps
from flask import redirect, url_for, flash, request
from flask_login import current_user


def permission_required(permission_check):
    """Decorator factory for permission checks.

    permission_check: callable that takes (current_user, **kwargs) and returns True/False
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                if not current_user.is_authenticated:
                    flash('Please log in to access this page.', 'error')
                    return redirect(url_for('login'))

                if not permission_check(current_user, **kwargs):
                    flash('You do not have permission to access this page.', 'error')
                    return redirect(url_for('dashboard'))

                return f(*args, **kwargs)
            except Exception:
                flash('Permission check failed.', 'error')
                return redirect(url_for('dashboard'))
        return wrapped
    return decorator


def roles_allowed(*roles):
    """Simple role-based decorator: checks if current_user.role in roles."""
    def check(user, **kwargs):
        return getattr(user, 'role', None) in roles

    return permission_required(check)


def company_required(company_id_param='company_id'):
    """Decorator that ensures current_user belongs to the given company (by id param name).

    Usage: @company_required('company_id')
    Expects route kwargs to include the company_id param.
    """
    def check(user, **kwargs):
        cid = kwargs.get(company_id_param) or request.args.get(company_id_param)
        if not cid:
            return False
        # If user has attribute company_id, compare; otherwise, allow (developer must adapt)
        return getattr(user, 'company_id', None) == int(cid)

    return permission_required(check)
