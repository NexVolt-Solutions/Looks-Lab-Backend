"""
Application configuration.
Environment variables and settings management using Pydantic.
"""
import secrets
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENV: str = "development"
    APP_NAME: str = "looks-lab"
    APP_URL: str | None = None
    CORS_ORIGINS: str | None = None
    TRUSTED_HOSTS: str | None = None

    DATABASE_URI: str

    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRATION_DAYS: int = 30

    LOCAL_STORAGE_PATH: str = "./media"
    AWS_REGION: str | None = None
    AWS_S3_BUCKET: str | None = None
    AWS_S3_PUBLIC_BUCKET: str | None = None
    AWS_S3_BASE_URL: str | None = None
    CLOUDFRONT_DOMAIN: str | None = None
    ASSET_BASE_URL: str | None = None
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None

    LOG_LEVEL: str = "INFO"
    ENABLE_REQUEST_LOGGING: bool = True
    ENABLE_SENTRY: bool = False
    SENTRY_DSN: str | None = None
    ENABLE_SECURITY_HEADERS: bool = True

    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-1.5-flash"

    EMAIL_PROVIDER: str = "ses"
    SES_REGION: str | None = None
    SES_SENDER: str | None = None
    SMTP_HOST: str | None = None
    SMTP_PORT: int | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None

    GOOGLE_CLIENT_ID: str
    APPLE_CLIENT_ID: str | None = None
    APPLE_TEAM_ID: str | None = None
    APPLE_KEY_ID: str | None = None
    APPLE_PRIVATE_KEY: str | None = None

    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def is_production(self) -> bool:
        return self.ENV.lower() in ("production", "prod")

    @property
    def is_development(self) -> bool:
        return self.ENV.lower() in ("development", "dev")

    @property
    def use_s3(self) -> bool:
        return bool(self.AWS_S3_BUCKET and self.AWS_ACCESS_KEY_ID and self.AWS_SECRET_ACCESS_KEY)

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.CORS_ORIGINS:
            if self.is_development:
                return [
                    "http://localhost:3000",
                    "http://localhost:8000",
                    "http://127.0.0.1:3000",
                    "http://127.0.0.1:8000"
                ]
            return []
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def trusted_hosts_list(self) -> list[str]:
        if not self.TRUSTED_HOSTS:
            return ["*"] if self.is_development else []
        return [h.strip() for h in self.TRUSTED_HOSTS.split(",") if h.strip()]

    @property
    def google_client_id(self) -> str:
        return self.GOOGLE_CLIENT_ID

    @property
    def apple_client_id(self) -> str | None:
        return self.APPLE_CLIENT_ID

    def validate_settings(self) -> None:
        errors = []

        if not self.DATABASE_URI:
            errors.append("DATABASE_URI is required")

        if not self.JWT_SECRET:
            errors.append("JWT_SECRET is required")
        elif len(self.JWT_SECRET) < 32:
            errors.append("JWT_SECRET must be at least 32 characters for security")

        if not self.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is required for AI processing")

        if not self.GOOGLE_CLIENT_ID:
            errors.append("GOOGLE_CLIENT_ID is required for Google OAuth")

        if self.is_production:
            if not self.CORS_ORIGINS:
                errors.append("CORS_ORIGINS must be explicitly set in production")

            if not self.TRUSTED_HOSTS:
                errors.append("TRUSTED_HOSTS must be explicitly set in production")

            if self.use_s3:
                if not self.AWS_REGION:
                    errors.append("AWS_REGION is required when using S3")
                if not self.AWS_ACCESS_KEY_ID:
                    errors.append("AWS_ACCESS_KEY_ID is required when using S3")
                if not self.AWS_SECRET_ACCESS_KEY:
                    errors.append("AWS_SECRET_ACCESS_KEY is required when using S3")

            if self.ENABLE_SENTRY and not self.SENTRY_DSN:
                errors.append("SENTRY_DSN is required when ENABLE_SENTRY is True")

        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)

    @staticmethod
    def generate_secret_key() -> str:
        return secrets.token_urlsafe(32)


settings = Settings()

