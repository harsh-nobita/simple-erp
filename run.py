import os
from app import app, db

# -------------------------------
# Database configuration
# -------------------------------
# Use absolute path so SQLite works on Render and locally
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'erp.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_FILE}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# -------------------------------
# Determine environment
# -------------------------------
# If PORT env variable exists -> running on Render
is_render = os.environ.get("PORT") is not None

# Set debug mode
debug_mode = not is_render  # True locally, False on Render

# -------------------------------
# Create tables and test users
# -------------------------------
with app.app_context():
    db.create_all()  # Creates tables if they don't exist

    from app.models import User

    # Define test users with roles
    test_users = [
        {"username": "admin", "password": "adminpass", "role": "Admin"},
        {"username": "manager", "password": "managerpass", "role": "Manager"},
        {"username": "staff", "password": "staffpass", "role": "Staff"}
    ]

    for u in test_users:
        existing_user = User.query.filter_by(username=u["username"]).first()
        if not existing_user:
            user = User(username=u["username"], role=u["role"])
            user.set_password(u["password"])
            db.session.add(user)
            print(f"Created {u['role']} user: {u['username']} / {u['password']}")
        else:
            print(f"{u['role']} user already exists: {u['username']}")

    db.session.commit()

# -------------------------------
# Run server
# -------------------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Render provides PORT
    host = '0.0.0.0' if is_render else '127.0.0.1'
    
    print(f"Starting HNS ERP app on {host}:{port}, debug={debug_mode}")
    app.run(debug=debug_mode, host=host, port=port)
