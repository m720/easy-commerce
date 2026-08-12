from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

# Primary engine: every write, and every read that must observe a write made in
# the same request, goes here.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Optional read replica for catalogue traffic. Unset in development and in the
# default compose stack, in which case reads fall back to the primary — the
# routing seam exists either way, so adding a replica is a config change rather
# than a refactor. See docs/adr/0005-read-replica-routing.md.
read_engine = (
    create_engine(
        settings.DATABASE_REPLICA_URL,
        pool_pre_ping=True,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
    )
    if settings.DATABASE_REPLICA_URL
    else None
)
ReadSessionLocal = (
    sessionmaker(autocommit=False, autoflush=False, bind=read_engine)
    if read_engine is not None
    else None
)

Base = declarative_base()
