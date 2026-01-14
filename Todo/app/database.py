"""
Database connection and session management for Neon Serverless PostgreSQL.
"""
from sqlmodel import Session, create_engine
from sqlalchemy.pool import NullPool
from .config import settings

# Create SQLModel engine with connection pooling for Neon
# NullPool is recommended for serverless environments to avoid connection exhaustion
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.ENVIRONMENT == "development",
    poolclass=NullPool if settings.ENVIRONMENT == "production" else None,
)


def get_session():
    """
    Dependency function to get database session.
    Yields a session and ensures it's closed after use.
    """
    with Session(engine) as session:
        yield session
