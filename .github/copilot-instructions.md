---
description: "Guidelines for the Flask-based ERP system: modular blueprint architecture, consistent naming conventions, and coding patterns for CRM, Finance, and HRM modules"
---

# Flask ERP System Guidelines

## Code Style

Follow established patterns in [app/models.py](app/models.py), [app/routes.py](app/routes.py), and module-specific files.

- **Naming Conventions**:
  - Classes (models, forms): PascalCase, singular nouns (e.g., `Lead`, `EmployeeForm`)
  - Functions/methods: snake_case (e.g., `generate_lead_id()`, `calculate_order_total()`)
  - Variables/columns: snake_case, descriptive (e.g., `created_at`, `gross_pay`)
  - Database tables: lowercase plural via `__tablename__` (e.g., `"leads"`)
  - URL routes: lowercase with module prefixes (e.g., `/crm/leads`, `/finance/billing`)

- **Imports**: Group by standard library, third-party, local modules. Use relative imports within blueprints.

- **Docstrings**: Add for complex functions; keep simple for CRUD operations.

## Architecture

Modular Flask application with blueprints for scalability.

- **Structure**:
  - Core app in `app/` with shared models, routes, forms
  - Modules: `crm/`, `finance/`, `hrm/` each with models, routes, forms, templates, static files
  - Database: SQLAlchemy ORM with SQLite; relationships use `db.relationship()` with cascade deletes

- **Blueprints**: Register in [app/__init__.py](app/__init__.py) with custom template/static folders.

- **Models**: Define in `models.py` or `{module}_models.py`; use `UserMixin` for authentication.

- **Routes**: Use `@bp.route()` decorators; apply `@login_required` and role checks.

- **Forms**: WTForms with CSRF; validate with `form.validate_on_submit()`.

- **Templates**: Jinja2 in `templates/` and module subfolders; use Bootstrap for UI consistency.

## Build and Test

- **Run Locally**: `python run.py` (creates DB and test users)
- **Install Dependencies**: `pip install -r requirements.txt`
- **Test**: Run `pytest` in `tests/` directory
- **Deploy**: Gunicorn for production (Procfile for Render)

## Conventions

- **CRUD Patterns**: Form validation on POST, redirect-after-POST, flash messages for feedback.
- **Error Handling**: Use `abort(403/404)`, try-catch for type conversions, custom form validators; flash errors to users.
- **Security**: Role-based access (`Admin`, `Manager`, `Staff`); hash passwords with `werkzeug.security`.
- **Logging**: Minimal; use `print()` for debug; flash messages for user notifications (not logs).
- **Database**: Commit in try-catch blocks; prevent deletes with related records.
- **AJAX**: Check `X-Requested-With` header for partial responses.
- **Utilities**: Extract business logic to `{module}_utils.py` (e.g., ID generation).

Reference [README.md](README.md) and module-specific files for detailed examples.