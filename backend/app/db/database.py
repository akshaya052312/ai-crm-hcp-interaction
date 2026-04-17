"""
Database Connection & Session Management

Provides the SQLAlchemy engine, session factory, and dependency
for FastAPI route injection. Uses psycopg2 (sync) driver.
"""

import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.db.models import Base

# Load environment variables
load_dotenv()

# ── Configuration ───────────────────────────────────────────

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/crm_db"
)

# ── Engine ──────────────────────────────────────────────────

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,       # verify connections before checkout
    echo=False,               # set True for SQL query logging
)

# ── Session Factory ─────────────────────────────────────────

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# ── Table Creation ──────────────────────────────────────────

def init_db():
    """Create all tables defined in models.py.
    
    Intended for development / first-run setup.
    In production, use Alembic migrations instead.
    """
    Base.metadata.create_all(bind=engine)


# ── FastAPI Dependency ──────────────────────────────────────

def get_db() -> Session:
    """Yield a database session for FastAPI dependency injection.
    
    Usage in a route:
        @router.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
