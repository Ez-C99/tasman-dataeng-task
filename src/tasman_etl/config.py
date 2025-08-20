from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Toggle the Great Expectations Data Quality (DQ) checks
    # True blocks on failure, False logs and continues
    dq_enforce: bool = Field(
        default=True,
        validation_alias="DQ_ENFORCE",
    )
    # Database connection string for loader
    db_url: str = Field(
        default="postgresql://postgres:localpw@localhost:5432/usajobs",
        validation_alias="DB_URL",
    )

    # (Optional) make local .env loading explicit; safe in containers too.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
