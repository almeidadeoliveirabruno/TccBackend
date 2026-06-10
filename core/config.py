from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_PREFIX: str = "/api"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./database.db"

    # Em dev, permitir todas as origens para evitar erros de CORS.
    # Em produção, definir via .env com uma lista separada por vírgulas.
    ALLOWED_ORIGINS: str = "*"

    OPENAI_API_KEY: str = ""

    SECRET_KEY: str

    @field_validator("ALLOWED_ORIGINS")
    def parse_allowed_origins(cls, v: str) -> List[str]:
        if v == "*":
            return ["*"]
        return [origin.strip() for origin in v.split(",")] if v else []
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()