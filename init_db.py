from app import app, db
import os

def init_database():
    """Initialize the database tables"""
    with app.app_context():
        try:
            print("Creating database tables...")
            db.create_all()
            print("Database tables created successfully!")
            
            # Optionally check if the connection works
            from sqlalchemy import text
            result = db.session.execute(text("SELECT 1"))
            print("Database connection test passed!")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            import traceback
            traceback.print_exc()
            return False
    return True

if __name__ == "__main__":
    init_database()
