from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    DATABASE_URL: str
    BETTER_AUTH_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_DAYS: int = 7
    DEBUG: bool = False
    CORS_ORIGINS: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
