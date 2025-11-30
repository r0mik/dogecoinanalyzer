"""Database management utilities."""

import sys
from database.models import init_db, engine, Base
from utils.logger import setup_logger

logger = setup_logger('db_manager')


def initialize_database():
    """Initialize database schema."""
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False


if __name__ == '__main__':
    """CLI entry point for database initialization."""
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        success = initialize_database()
        sys.exit(0 if success else 1)
    else:
        print("Usage: python -m database.db_manager init")
        sys.exit(1)

