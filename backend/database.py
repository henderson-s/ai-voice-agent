from supabase import create_client, Client
from functools import lru_cache
from typing import Optional, Dict, Any
from backend.config import get_settings


@lru_cache()
def get_supabase_client() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_key)


class Database:
    def __init__(self):
        self.client = get_supabase_client()


def get_db() -> Database:
    return Database()

