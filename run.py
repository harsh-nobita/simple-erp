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
# Create tables and test user
# -------------------------------
with app.app_context():
    db.create_all()  # Creates tables if they don't exist

    from app.models import User

    # Auto-create test user if none exists
    if User.query.count() == 0:
        test_user = User(username='testuser')
        test_user.set_password('testpassword')
        db.session.add(test_user)
        db.session.commit()
        print("Test user created: testuser / testpassword")
    else:
        print("Test user already exists.")

# -------------------------------
# Run server
# -------------------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Render provides PORT
    host = '0.0.0.0' if is_render else '127.0.0.1'
    
    print(f"Starting ERP app on {host}:{port}, debug={debug_mode}")
    app.run(debug=debug_mode, host=host, port=port)
