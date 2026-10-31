"""Application settings loaded from environment variables (and an optional .env file)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SubLedger"
    debug: bool = False

    # Either provide a full DATABASE_URL, or the individual POSTGRES_* parts.
    database_url: str | None = None
    postgres_user: str | None = None
    postgres_password: str | None = None
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "subledger"

    # Number of days after issue date that an invoice becomes due.
    invoice_due_days: int = 14

    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.database_url:
            return self.database_url
        if not self.postgres_user or not self.postgres_password:
            raise ValueError(
                "Database is not configured. Set DATABASE_URL or POSTGRES_USER and POSTGRES_PASSWORD."
            )
        url = URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )
        return url.render_as_string(hide_password=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
