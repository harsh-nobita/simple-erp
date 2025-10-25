from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

# Create Flask app, specifying the template folder in the project root
app = Flask(__name__, template_folder='../templates')
app.config.from_object(Config)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect unauthenticated users to login
login_manager.login_message = 'Please log in to access this page.'

# User loader for Flask-Login (required to load user from session)
@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))

# Import routes after initialization to avoid circular imports
# Register HRM blueprint if present
try:
    from app.hrm import bp as hrm_bp
    app.register_blueprint(hrm_bp, url_prefix='/hrm')
except Exception:
    # If the hrm package isn't available yet, skip registration.
    # This keeps the app import-safe during incremental development.
    pass

# Register Finance blueprint if present
try:
    from app.finance import bp as finance_bp
    app.register_blueprint(finance_bp, url_prefix='/finance')
except Exception:
    # Keep import-safe during incremental development
    pass

# Import other routes after initialization to avoid circular imports
from app import routes

# Optional: Debug print (remove after testing)
print(f"Template folder set to: {app.template_folder}")
print(f"Full template path: {app.root_path}/../templates")  # Should point to your templates