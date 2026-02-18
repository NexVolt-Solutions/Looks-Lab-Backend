"""
Application configuration.
Environment variables and settings management using Pydantic.
"""
import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── General ───────────────────────────────────────────────
    ENV: str = "development"
    APP_NAME: str = "looks-lab"
    APP_URL: str | None = None
    CORS_ORIGINS: str | None = None
    TRUSTED_HOSTS: str | None = None

    # ── Database ──────────────────────────────────────────────
    DATABASE_URI: str

    # ── Cache ─────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT / Security ────────────────────────────────────────
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    JWT_REFRESH_SECRET: str = ""
    REFRESH_TOKEN_EXPIRATION_DAYS: int = 30

    # ── File Storage ──────────────────────────────────────────
    LOCAL_STORAGE_PATH: str = "./media"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/webp"

    AWS_REGION: str | None = None
    AWS_S3_BUCKET: str | None = None
    AWS_S3_PUBLIC_BUCKET: str | None = None
    AWS_S3_BASE_URL: str | None = None
    CLOUDFRONT_DOMAIN: str | None = None
    ASSET_BASE_URL: str | None = None
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None

    # ── Logging / Monitoring ──────────────────────────────────
    LOG_LEVEL: str = "INFO"
    ENABLE_REQUEST_LOGGING: bool = True
    ENABLE_SENTRY: bool = False
    SENTRY_DSN: str | None = None
    ENABLE_SECURITY_HEADERS: bool = True

    # ── AI ────────────────────────────────────────────────────
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-3-flash-preview" 

    # ── Email ─────────────────────────────────────────────────
    EMAIL_PROVIDER: str = "ses"
    SES_REGION: str | None = None
    SES_SENDER: str | None = None
    SMTP_HOST: str | None = None
    SMTP_PORT: int | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None

    # ── Social Login ──────────────────────────────────────────
    GOOGLE_CLIENT_ID: str
    APPLE_CLIENT_ID: str | None = None
    APPLE_TEAM_ID: str | None = None
    APPLE_KEY_ID: str | None = None
    APPLE_PRIVATE_KEY: str | None = None

    # ── Rate Limiting ─────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60

    # ── Helper Properties ─────────────────────────────────────

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENV.lower() in ("production", "prod")

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENV.lower() in ("development", "dev")

    @property
    def use_s3(self) -> bool:
        """Check if S3 storage is configured and should be used."""
        return bool(
            self.AWS_S3_BUCKET
            and self.AWS_ACCESS_KEY_ID
            and self.AWS_SECRET_ACCESS_KEY
        )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        if not self.CORS_ORIGINS:
            if self.is_development:
                return [
                    "http://localhost:3000",
                    "http://localhost:8000",
                    "http://127.0.0.1:3000",
                    "http://127.0.0.1:8000",
                ]
            return []
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def trusted_hosts_list(self) -> list[str]:
        """Parse trusted hosts from comma-separated string."""
        if not self.TRUSTED_HOSTS:
            return ["*"] if self.is_development else []
        return [h.strip() for h in self.TRUSTED_HOSTS.split(",") if h.strip()]

    @property
    def allowed_image_types_list(self) -> list[str]:
        """Parse allowed image MIME types from comma-separated string."""
        return [t.strip() for t in self.ALLOWED_IMAGE_TYPES.split(",") if t.strip()]

    @property
    def max_file_size_bytes(self) -> int:
        """Convert MAX_FILE_SIZE_MB to bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def jwt_refresh_secret(self) -> str:
        """Get refresh token secret, fallback to JWT_SECRET if not set."""
        return self.JWT_REFRESH_SECRET or self.JWT_SECRET

    # ── Validation ────────────────────────────────────────────

    def validate_settings(self) -> None:
        """
        Validate required settings based on environment.
        Raises ValueError if critical settings are missing.
        """
        errors = []

        # Always required
        if not self.DATABASE_URI:
            errors.append("DATABASE_URI is required")

        if not self.JWT_SECRET:
            errors.append("JWT_SECRET is required")
        elif len(self.JWT_SECRET) < 32:
            errors.append("JWT_SECRET must be at least 32 characters")

        if not self.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is required for AI processing")

        if not self.GOOGLE_CLIENT_ID:
            errors.append("GOOGLE_CLIENT_ID is required for Google OAuth")

        # Production-specific requirements
        if self.is_production:
            if not self.CORS_ORIGINS:
                errors.append("CORS_ORIGINS must be set in production")
            if not self.TRUSTED_HOSTS:
                errors.append("TRUSTED_HOSTS must be set in production")
            if not self.JWT_REFRESH_SECRET:
                errors.append("JWT_REFRESH_SECRET must be set in production")

            # S3 validation (if enabled)
            if self.use_s3:
                if not self.AWS_REGION:
                    errors.append("AWS_REGION is required when using S3")
                if not self.AWS_ACCESS_KEY_ID:
                    errors.append("AWS_ACCESS_KEY_ID is required when using S3")
                if not self.AWS_SECRET_ACCESS_KEY:
                    errors.append("AWS_SECRET_ACCESS_KEY is required when using S3")

            # Sentry validation (if enabled)
            if self.ENABLE_SENTRY and not self.SENTRY_DSN:
                errors.append("SENTRY_DSN is required when ENABLE_SENTRY is True")

        if errors:
            error_msg = (
                "Configuration validation failed:\n"
                + "\n".join(f"  - {e}" for e in errors)
            )
            raise ValueError(error_msg)

    @staticmethod
    def generate_secret_key() -> str:
        """Generate a cryptographically secure random secret key."""
        return secrets.token_urlsafe(32)


# Initialize settings and validate on import
settings = Settings()
settings.validate_settings()

