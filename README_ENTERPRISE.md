# Enterprise Expansion Notes

This document summarizes the enterprise-grade features added as scaffolding and recommended next steps.

Included changes:
- `app/enterprise_models.py` — Company, Department and user-department relationships (DB models).
- `app/security.py` — Generic decorators `roles_allowed` and `permission_required` to build RBAC checks.
- `app/backup.py` — Simple SQLite backup/restore helpers.
- `app/notifications.py` — Minimal email sender and SMS/WhatsApp placeholders.
- `static/css/enterprise.css` — Compact layout, color palette, and module accents.
- `business/` folder — Pricing, licensing README, and subscription integration steps.
- `docs/scalability.md` — Caching, async jobs, logging, and multi-tenant recommendations.

Next steps to fully enable:
- Generate and run database migrations (Flask-Migrate) to add new tables to the DB.
- Integrate a transactional email provider (SendGrid/Mailgun) or use Flask-Mail for SMTP.
- Implement background worker (Celery/RQ) and move heavy tasks there (PDF generation, backups, notifications).
- Implement analytics endpoints that aggregate data and cache results for dashboard charts.
