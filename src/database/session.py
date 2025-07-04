# src/database/session.py
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       
    pool_size=10,            
    max_overflow=20
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    """Dependency function for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# For direct usage in services (without dependency injection)
def get_db_session():
    """Get a database session for direct usage"""
    return SessionLocal()