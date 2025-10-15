"""
Database client and connection management.
"""
import logging
from functools import lru_cache
from typing import Dict, Any, List, Optional

from supabase import create_client, Client

from backend.config import get_settings


logger = logging.getLogger(__name__)


@lru_cache()
def get_supabase_client() -> Client:
    """
    Get cached Supabase client instance.

    Returns:
        Client: Supabase client configured with service key
    """
    settings = get_settings()
    logger.info("Initializing Supabase client")
    return create_client(settings.supabase_url, settings.supabase_service_key)


class Database:
    """
    Database wrapper providing convenient access to Supabase client.
    """

    def __init__(self):
        """Initialize database with Supabase client."""
        self.client = get_supabase_client()
        logger.debug("Database instance created")


def get_db() -> Database:
    """
    Dependency injection function for FastAPI routes.

    Returns:
        Database: Database instance
    """
    return Database()
