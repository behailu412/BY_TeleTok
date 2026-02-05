import os
from app import app, db

def setup_database():
    """Create database tables using SQLAlchemy"""
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Error creating database tables: {e}")

if __name__ == "__main__":
    setup_database()