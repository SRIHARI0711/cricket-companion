"""
Async MySQL connection pool management.
The pool is created once on startup and shared across requests.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aiomysql

from config import settings

# Module-level pool reference
_pool: aiomysql.Pool | None = None


async def create_pool() -> None:
    """Create the global connection pool. Called during app startup."""
    global _pool
    _pool = await aiomysql.create_pool(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        db=settings.DB_NAME,
        autocommit=True,
        charset="utf8mb4",
        minsize=2,
        maxsize=10,
        cursorclass=aiomysql.DictCursor,  # Return rows as dicts automatically
    )


async def close_pool() -> None:
    """Close the global connection pool. Called during app shutdown."""
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None


@asynccontextmanager
async def get_connection() -> AsyncGenerator[aiomysql.Connection, None]:
    """Async context manager that yields a connection from the pool."""
    if _pool is None:
        raise RuntimeError("Database pool is not initialised. Did the app start correctly?")
    async with _pool.acquire() as conn:
        yield conn
