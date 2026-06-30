from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://recipe_user:recipe_password@localhost:5432/recipe_rescue"
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:8080"]
    seed_demo_data: bool = True
    auth_secret: str = "change-this-local-development-secret"
    access_token_expire_minutes: int = 1440

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
