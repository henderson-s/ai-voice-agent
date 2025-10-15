from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from pathlib import Path


# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    supabase_service_key: str
    retell_api_key: str
    
    class Config:
        env_file = str(ENV_FILE)
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    if not ENV_FILE.exists():
        raise FileNotFoundError(
            f"\n\n❌ .env file not found at: {ENV_FILE}\n\n"
            f"Please create a .env file in the project root with:\n"
            f"  SUPABASE_URL=your_supabase_url\n"
            f"  SUPABASE_KEY=your_supabase_anon_key\n"
            f"  SUPABASE_SERVICE_KEY=your_supabase_service_key\n"
            f"  RETELL_API_KEY=your_retell_api_key\n"
        )
    return Settings()

