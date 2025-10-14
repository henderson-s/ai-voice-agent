from supabase import create_client, Client
from functools import lru_cache
from typing import Optional, Dict, Any, List
from backend.config import get_settings


@lru_cache()
def get_supabase_client() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_key)


class Database:
    def __init__(self):
        self.client = get_supabase_client()
    
    async def create_user(self, email: str, hashed_password: str, full_name: str) -> Dict[str, Any]:
        response = self.client.table("users").insert({
            "email": email,
            "password_hash": hashed_password,
            "full_name": full_name
        }).execute()
        return response.data[0]
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        response = self.client.table("users").select("*").eq("email", email).execute()
        return response.data[0] if response.data else None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        response = self.client.table("users").select("*").eq("id", user_id).execute()
        return response.data[0] if response.data else None


def get_db() -> Database:
    return Database()

