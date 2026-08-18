from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    environment: str = "development"
    port: int = 8001
    primary_backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
