from typing import Optional, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Environment
    ENV: str = "development"
    APP_NAME: str = "looks-lab"
    APP_URL: Optional[str] = None
    CORS_ORIGINS: Optional[str] = None
    TRUSTED_HOSTS: Optional[str] = None

    # Database
    # For local testing, default is provided. Remove default in production.
    DATABASE_URI: str = "postgresql://looks_lab:lab3344@localhost:5432/looks_lab"

    # Cache / Queue
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT / Security
    # For local testing, default is provided. Change in production!
    JWT_SECRET: str = "dev-secret-key-change-in-production-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRATION_DAYS: int = 30

    # Storage (local or AWS S3)
    LOCAL_STORAGE_PATH: str = "./media"
    AWS_REGION: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None
    AWS_S3_PUBLIC_BUCKET: Optional[str] = None
    AWS_S3_BASE_URL: Optional[str] = None
    CLOUDFRONT_DOMAIN: Optional[str] = None
    ASSET_BASE_URL: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    # Logging / Monitoring
    LOG_LEVEL: str = "INFO"
    ENABLE_REQUEST_LOGGING: bool = True
    ENABLE_SENTRY: bool = False
    SENTRY_DSN: Optional[str] = None
    ENABLE_SECURITY_HEADERS: bool = True

    # AI / External APIs
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Email
    EMAIL_PROVIDER: str = "ses"
    SES_REGION: Optional[str] = None
    SES_SENDER: Optional[str] = None
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # Social Login
    GOOGLE_CLIENT_ID: Optional[str] = None
    APPLE_CLIENT_ID: Optional[str] = None
    APPLE_TEAM_ID: Optional[str] = None
    APPLE_KEY_ID: Optional[str] = None
    APPLE_PRIVATE_KEY: Optional[str] = None

    # Rate limiting / security
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    # Convenience properties
    @property
    def is_production(self) -> bool:
        return self.ENV.lower() in ("production", "prod")

    @property
    def use_s3(self) -> bool:
        return bool(self.AWS_S3_BUCKET and self.is_production)

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return []
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def trusted_hosts_list(self) -> List[str]:
        # In dev, if unset, allow anything (avoids breaking local/testing).
        if not self.TRUSTED_HOSTS:
            return ["*"] if not self.is_production else []
        return [h.strip() for h in self.TRUSTED_HOSTS.split(",") if h.strip()]

    def validate_settings(self) -> None:
        """Validate required settings at startup."""
        errors = []
        
        # Required in all environments
        # For local testing, these are optional. Uncomment for production.
        # if not self.DATABASE_URI:
        #     errors.append("DATABASE_URI is required")
        # if not self.JWT_SECRET:
        #     errors.append("JWT_SECRET is required (set JWT_SECRET in .env file)")
        
        # Production-specific requirements - COMMENTED OUT FOR LOCAL TESTING
        # Uncomment when deploying to production
        # if self.is_production:
        #     if not self.CORS_ORIGINS:
        #         errors.append(
        #             "CORS_ORIGINS must be set in production. "
        #             "Set ENV=development for local development."
        #         )
        #     if not self.TRUSTED_HOSTS:
        #         errors.append(
        #             "TRUSTED_HOSTS must be set in production. "
        #             "Set ENV=development for local development."
        #         )
        #     if self.JWT_SECRET and len(self.JWT_SECRET) < 32:
        #         errors.append("JWT_SECRET must be at least 32 characters in production")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)


settings = Settings()

