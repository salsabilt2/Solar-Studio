from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./solar_studio.db"
    secret_key: str = "local-development-change-me-at-least-32-characters"
    app_env: str = "development"
    invite_code: str = ""
    allow_public_signup: bool = True
    admin_email: str = ""
    admin_password: str = ""
    openai_api_key: str = ""
    openai_answer_model: str = "gpt-5-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    ai_monthly_limit_usd: float = 5.0
    resend_api_key: str = ""
    email_from: str = ""
    smtp_host: str = ""
    smtp_port: int = 1025
    scheduler_secret: str = ""
    public_url: str = "http://localhost:5173"

    @field_validator("database_url")
    @classmethod
    def use_psycopg(cls, value: str) -> str:
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value


settings = Settings()
