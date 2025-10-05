from app import app, db
import os

if __name__ == '__main__':
    print("Starting app...")
    with app.app_context():
        print("App context active. Creating tables...")
        db.create_all()  # Creates tables
        
        # Verify DB path and creation
        db_path = 'erp.db'
        print(f"DB URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"Expected DB path: {os.path.abspath(db_path)}")
        
        # Test: Check if User table exists by counting rows (forces connection)
        from app.models import User
        user_count = User.query.count()
        print(f"User table created. Rows: {user_count}")
        
        # Auto-create test user if none exists
        if user_count == 0:
            from app.models import User
            test_user = User(username='testuser')
            test_user.set_password('testpassword')
            db.session.add(test_user)
            db.session.commit()
            print("Test user created: testuser / testpassword")
        else:
            print("Test user already exists.")
    
    print("DB setup complete. Running server...")
    app.run(debug=True, host='127.0.0.1', port=5000)