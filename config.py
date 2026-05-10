import os

class Config:
    # Secret key for sessions (generate a new one for production)
    SECRET_KEY = os.environ.get('SECRET_KEY') or b'your-secret-key-here-change-this'  # Change to a random string

    # Database configuration (SQLite for local dev, full URL for root location)
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(os.path.dirname(__file__), "erp.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids performance overhead