"""
Database module — re-exports from db_gate for backward compatibility.

All new code should import from src.core.db_gate directly.
This module exists so existing imports (models, alembic, etc.) continue to work.
"""
from src.core.db_gate import Base, get_db, get_read_db, db_gate

# Re-export for alembic and models
__all__ = ["Base", "get_db", "get_read_db", "db_gate"]
