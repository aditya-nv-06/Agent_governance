from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Defaults are development-friendly; production values should be provided
    # via environment variables or `.env.production` in your deployment.
    environment: str = "development"
    port: int = 8001
    primary_backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"
    service_url: str = "http://localhost:8001"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
