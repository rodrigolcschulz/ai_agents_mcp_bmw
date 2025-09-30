"""
Database configuration and connection management
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'ai_data_engineering',
    'user': 'postgres',
    'password': 'postgres123'
}

# Create database URL
DATABASE_URL = f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"

# Create engine with encoding settings
engine = create_engine(
    DATABASE_URL, 
    echo=True,
    connect_args={
        "client_encoding": "utf8",
        "options": "-c client_encoding=utf8 -c timezone=America/Sao_Paulo",
        "application_name": "ai_data_engineering"
    },
    pool_pre_ping=True,
    pool_recycle=300
)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """Test database connection"""
    try:
        import psycopg2
        
        # Simple connection test
        conn = psycopg2.connect(**DATABASE_CONFIG)
        
        # Test a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        
        conn.close()
        return True
        
    except Exception:
        return False
