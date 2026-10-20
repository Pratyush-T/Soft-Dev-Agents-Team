"""SQLAlchemy 2.0 async engine and session management with SQLite WAL pragmas."""
from typing import AsyncGenerator
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

engine = create_async_engine(
    settings.PRONET_DATABASE_URL,
    echo=False,
    connect_args={"timeout": settings.PRONET_SQLITE_BUSY_TIMEOUT_MS / 1000.0}
)


@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enforce SQLite WAL mode, foreign keys, and busy timeout on every leased connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode = WAL;")
    cursor.execute("PRAGMA synchronous = NORMAL;")
    cursor.execute(f"PRAGMA busy_timeout = {settings.PRONET_SQLITE_BUSY_TIMEOUT_MS};")
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("PRAGMA cache_size = -64000;")
    cursor.execute("PRAGMA temp_store = MEMORY;")
    cursor.close()


async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing an async database session per request."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables from SQLAlchemy metadata."""
    from app.models.schema import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
