from app import app, db
import os

if __name__ == '__main__':
    print("Starting app...")
    with app.app_context():
        print("App context active. Creating tables...")
        db.create_all()
        
        # Optional: Auto-create test user
        from app.models import User
        if User.query.count() == 0:
            test_user = User(username='testuser')
            test_user.set_password('testpassword')
            db.session.add(test_user)
            db.session.commit()
            print("Test user created: testuser / testpassword")
        else:
            print("Test user already exists.")

    print("DB setup complete. Running server...")

    # Use port from environment variable if exists (required on platforms like Render)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
