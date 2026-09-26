from typing import List, Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_PREFIX: str = "/api"
    DEBUG: bool = True

    # Configuração de Banco de Dados
    DB_TARGET: str = "local"  # "local" ou "neon"
    DATABASE_URL_LOCAL: str = "postgresql://postgres:postgres@localhost:5432/odontolink"
    DATABASE_URL_NEON: Optional[str] = None
    DATABASE_URL: Optional[str] = None

    # Em dev, permitir todas as origens para evitar erros de CORS.
    # Em produção, definir via .env com uma lista separada por vírgulas.
    ALLOWED_ORIGINS: str = "*"

    OPENAI_API_KEY: str = ""

    SECRET_KEY: str

    CPF_ENCRYPTION_KEY: str

    CPF_HASH_PEPPER: str

    @model_validator(mode="after")
    def assemble_db_url(self):
        if self.DB_TARGET.lower() == "neon" and self.DATABASE_URL_NEON:
            self.DATABASE_URL = self.DATABASE_URL_NEON
        elif self.DB_TARGET.lower() == "local":
            self.DATABASE_URL = self.DATABASE_URL_LOCAL
        elif not self.DATABASE_URL:
            self.DATABASE_URL = self.DATABASE_URL_LOCAL
        return self

    @field_validator("ALLOWED_ORIGINS")
    def parse_allowed_origins(cls, v: str) -> List[str]:
        if v == "*":
            return ["*"]
        return [origin.strip() for origin in v.split(",")] if v else []
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"

settings = Settings()