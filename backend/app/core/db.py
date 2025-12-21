import asyncio
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool
from backend.app.core.config import settings
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from backend.app.core.logging import get_logger
from backend.app.core.model_registery import load_models

logger = get_logger()

engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=AsyncAdaptedQueuePool,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session = async_session()
    try:
        yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        if session:
            try:
                await session.rollback()
                logger.info("Database session rollback successful.")
            except Exception as rollback_error:
                logger.error(f"Database session rollback failed: {rollback_error}")
        raise
    finally:
        if session:
            try:
                await session.close()
                logger.info("Database session closed successfully.")
            except Exception as close_error:
                logger.error(f"Database session close failed: {close_error}")
async def init_db() -> None:
    try:
        load_models()
        logger.info("Model loaded successfully")
        max_retries = 5
        retry_delay = 5  # seconds
        for attempt in range(max_retries):
            try:
                async with engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
                logger.info("Database connection established successfully.")
                return
            except Exception as e:
                logger.error(f"Database connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    raise
                logger.warn(f"Retrying database connection in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay * (attempt + 1))
    except Exception as final_error:
        logger.critical(f"Failed to establish database connection after {max_retries} attempts: {final_error}")
        raise