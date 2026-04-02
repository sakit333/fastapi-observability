from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

class Settings:
    TEMPO_ENDPOINT: str = os.getenv("TEMPO_ENDPOINT", "http://tempo:4317")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_PATH: str = os.getenv("LOG_PATH", "/app/logs/app.log")

    # PostgreSQL settings
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_DB = os.getenv("POSTGRES_DB", "fastapi_db")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "fastapi_user")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "fastapi_password")

    # Redis settings
    REDIS_HOST = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))

    # JWT settings
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30))

settings = Settings()

