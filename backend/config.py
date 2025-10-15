"""
Application configuration and settings management.
"""
import os
import logging
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings


# Get backend directory (where this file is located)
BACKEND_DIR = Path(__file__).parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Supabase Configuration
    supabase_url: str
    supabase_key: str
    supabase_service_key: str

    # Retell AI Configuration
    retell_api_key: str

    # Server Configuration
    port: int = 8000
    host: str = "0.0.0.0"
    environment: str = "development"

    # Logging Configuration
    log_level: str = "INFO"

    class Config:
        env_file = str(ENV_FILE)
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.

    Returns:
        Settings: Application settings instance

    Raises:
        FileNotFoundError: If .env file is not found
    """
    if not ENV_FILE.exists():
        raise FileNotFoundError(
            f"\n\n❌ .env file not found at: {ENV_FILE}\n\n"
            f"Please create a .env file in the backend directory with:\n"
            f"  SUPABASE_URL=your_supabase_url\n"
            f"  SUPABASE_KEY=your_supabase_anon_key\n"
            f"  SUPABASE_SERVICE_KEY=your_supabase_service_key\n"
            f"  RETELL_API_KEY=your_retell_api_key\n"
        )
    return Settings()


def setup_logging() -> None:
    """
    Configure application-wide logging.
    """
    settings = get_settings()

    # Configure logging format
    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "%(funcName)s:%(lineno)d - %(message)s"
    )

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
        ]
    )

    # Set third-party library log levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


# Initialize settings on import
settings = get_settings()
