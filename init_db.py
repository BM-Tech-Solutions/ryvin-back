"""
Database initialization script to create all tables
"""
from app.core.database import Base, engine
from app.models.user import User
from app.models.token import RefreshToken

# Import all models here to ensure they are registered with SQLAlchemy
# Add any other models that need to be created

def init_db():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()
