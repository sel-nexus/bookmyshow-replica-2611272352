"""Load environment-backed application settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Represent validated runtime configuration for the API.

    Args:
        BaseSettings: Read fields from process environment and a local env file.
    """

    database_url: str = Field(alias="DATABASE_URL")
    db_name: str = Field(alias="DB_NAME", min_length=1)
    jwt_secret: str = Field(alias="JWT_SECRET", min_length=32)
    jwt_issuer: str = Field(alias="JWT_ISSUER", min_length=1)
    jwt_audience: str = Field(alias="JWT_AUDIENCE", min_length=1)
    jwt_expires_seconds: int = Field(default=1800, alias="JWT_EXPIRES_SECONDS", ge=1)
    demo_otp: str = Field(default="1234", alias="DEMO_OTP", min_length=1)
    cors_origins_raw: str = Field(default="http://localhost:4200", alias="CORS_ORIGINS")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    @property
    def cors_origins(self) -> list[str]:
        """Split configured browser origins into an explicit origin list.

        Returns:
            A list of non-empty allowed origins.
        """
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide validated settings instance.

    Returns:
        The cached application settings.
    """
    return Settings()
