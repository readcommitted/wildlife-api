"""
db.py — Database Engine & Session Setup
----------------------------------------

This module initializes the SQLAlchemy database connection and provides
session management for the Wildlife Vision System.

Features:
- Creates database engine using DATABASE_URL from project settings
- Defines `SessionLocal` for transaction management
- Provides `init_db()` to create tables based on ORM models

Intended for:
- Centralized database connection setup
- Reusable session handling across all modules

Dependencies:
- SQLAlchemy for ORM and engine management
- Project settings for environment-based configuration

Author: Matt Scardino
Project: Wildlife Vision System
"""

from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import dotenv
import os
from sqlalchemy.pool import QueuePool

dotenv.load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", None)

# --- ORM Base Class ---
Base = declarative_base()

# --- Database Engine ---
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,        # Default, but explicit is better
    pool_size=5,                # Number of persistent connections
    max_overflow=10,            # Extra connections allowed beyond pool_size
    pool_timeout=30,            # Max seconds to wait for connection
    pool_recycle=60,          # Recycle connections after 30 min
    pool_pre_ping=True          # Check if connection is alive before using
)


# --- Session Factory ---
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """
    Initializes the database by creating all tables defined in ORM models.
    Safe to run multiple times; only creates tables if they don't exist.
    """
    Base.metadata.create_all(engine)



