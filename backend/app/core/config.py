from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    model_config = SettingsConfigDict(
        env_file="../../.env/.env.local",
        env_ignore_empty=True,
        extra="ignore", 
        env_file_encoding="utf-8",
    )
    API_V1_STR: str = ""
    PROJECT_NAME: str = ""
    PROJECT_DESCTIPTION: str = ""
    SITE_NAME: str = ""
    DATABASE_URL: str = ""

settings = Settings() 