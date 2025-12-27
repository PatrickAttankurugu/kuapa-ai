"""
Database connection and session management for Kuapa AI
Uses PostgreSQL with pgVector for user profiles and conversation history
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
import logging

from .config import DATABASE_URL

logger = logging.getLogger("kuapa_ai")

# Create SQLAlchemy engine
engine = None
SessionLocal = None
Base = declarative_base()

def init_db():
    """Initialize database connection"""
    global engine, SessionLocal
    
    if not DATABASE_URL:
        logger.warning("DATABASE_URL not set - database features disabled")
        return False
    
    try:
        # Create engine with connection pooling
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,  # Enable connection health checks
            pool_size=10,
            max_overflow=20,
            echo=False  # Set to True for SQL query logging
        )
        
        # Create session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        logger.info("Database connection established successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
        return False

def get_db() -> Session:
    """
    Get database session
    Usage in FastAPI endpoints:
    
    @app.get("/endpoint")
    def endpoint(db: Session = Depends(get_db)):
        # Use db here
        pass
    """
    if not SessionLocal:
        logger.error("Database not initialized - call init_db() first")
        return None
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """
    Get database session as context manager
    Usage:
    
    with get_db_context() as db:
        # Use db here
        pass
    """
    if not SessionLocal:
        logger.error("Database not initialized")
        yield None
        return
    
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}", exc_info=True)
        raise
    finally:
        db.close()

def close_db():
    """Close database connection"""
    global engine
    if engine:
        engine.dispose()
        logger.info("Database connection closed")

def check_db_health() -> bool:
    """Check if database connection is healthy"""
    if not engine:
        return False
    
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False
