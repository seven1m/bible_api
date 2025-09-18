"""Centralized configuration using environment variables.
This mirrors the idea of appsettings + strongly typed configuration in C#.
"""
from pydantic import BaseModel
from functools import lru_cache
import os

class Settings(BaseModel):
    azure_storage_connection_string: str
    azure_container_name: str = "bible-translations"
    environment: str = os.getenv("ENVIRONMENT", "development")

    class Config:
        arbitrary_types_allowed = True

@lru_cache
def get_settings() -> Settings:
    # Pull raw envs; pydantic model will validate required ones
    conn = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not conn:
        # Leave it empty so FastAPI init can still happen; consumers decide how to fail
        conn = ""
    return Settings(
        azure_storage_connection_string=conn,
        azure_container_name=os.getenv("AZURE_CONTAINER_NAME", "bible-translations"),
        environment=os.getenv("ENVIRONMENT", "development"),
    )
