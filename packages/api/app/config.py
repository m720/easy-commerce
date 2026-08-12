from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/ecommerce"
    # Optional read replica. Catalogue reads are routed here when set; every
    # write and every read-your-own-write path stays on the primary.
    # See docs/adr/0005-read-replica-routing.md.
    DATABASE_REPLICA_URL: Optional[str] = None
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: Optional[str] = None
    S3_PRESIGNED_URL_EXPIRY: int = 3600

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "noreply@example.com"
    # Bounded so an unreachable mail host cannot pin a background-task thread.
    SMTP_TIMEOUT: int = 10

    # Admin
    ADMIN_EMAIL: Optional[str] = None

    # App
    DEBUG: bool = False
    # Public origin of this API. Used to build absolute URLs for locally served
    # assets such as the seeded product photos under /static.
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    # Observability
    SERVICE_NAME: str = "ecommerce-api"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    # "json" for machine-parseable logs (prod), "console" for readable dev logs.
    LOG_FORMAT: str = "json"
    METRICS_ENABLED: bool = True
    # Header carrying the correlation ID across service hops.
    REQUEST_ID_HEADER: str = "X-Request-ID"

    # Cache (Redis). Falls back to a no-op cache when REDIS_URL is unset or
    # Redis is unreachable — the API degrades to direct DB reads, never errors.
    REDIS_URL: Optional[str] = None
    CACHE_ENABLED: bool = True
    CACHE_TTL_PRODUCT_LIST: int = 60
    CACHE_TTL_PRODUCT_DETAIL: int = 300

    # Rate limiting (auth endpoints). Uses Redis when available, otherwise an
    # in-process fallback that only protects a single worker.
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_LOGIN_MAX: int = 10
    RATE_LIMIT_LOGIN_WINDOW: int = 300
    RATE_LIMIT_REGISTER_MAX: int = 5
    RATE_LIMIT_REGISTER_WINDOW: int = 3600

    # Idempotency. How long a completed checkout response stays replayable.
    IDEMPOTENCY_TTL_HOURS: int = 24
    # Reject POST /orders without an Idempotency-Key header. Off by default so
    # existing clients keep working; turn on once every client sends one.
    IDEMPOTENCY_REQUIRED: bool = False


settings = Settings()
