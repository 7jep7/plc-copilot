"""Development script to initialize the database."""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.core.database import init_db_safe
from app.core.config import settings

if __name__ == "__main__":
    print(f"Initializing database: {settings.DATABASE_URL}")
    init_db_safe()
    print("Database initialized successfully!")