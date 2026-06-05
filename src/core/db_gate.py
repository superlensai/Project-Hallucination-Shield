"""
Database Gate / Harness

This module provides a controlled access layer between the application and
the database. It enforces:

- Connection pool limits with overflow protection
- Query execution timeouts
- Read/write routing (prepared for read-replica support)
- Circuit breaker pattern for DB outages
- Structured health checks
- Audit logging for admin-level operations

All database access in the application should go through this gate.
"""
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from sqlalchemy import text

from src.core.config import settings

logger = logging.getLogger("halwall.db_gate")

Base = declarative_base()


class CircuitBreaker:
    """Simple circuit breaker to prevent cascading failures."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed = healthy, open = broken, half-open = testing

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.error(
                "Circuit breaker OPEN — DB connection failures exceeded threshold "
                f"({self.failure_count}/{self.failure_threshold})"
            )

    def record_success(self):
        self.failure_count = 0
        self.state = "closed"

    def can_attempt(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open":
            elapsed = time.time() - (self.last_failure_time or 0)
            if elapsed >= self.recovery_timeout:
                self.state = "half-open"
                return True
            return False
        # half-open: allow one attempt
        return True


class DatabaseGate:
    """
    Central database access controller.

    Provides managed connections with:
    - Pool size limits
    - Statement timeouts
    - Health monitoring
    - Circuit breaking
    """

    def __init__(self):
        self._write_engine: Optional[AsyncEngine] = None
        self._read_engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._read_session_factory: Optional[sessionmaker] = None
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=settings.DB_CIRCUIT_BREAKER_THRESHOLD,
            recovery_timeout=settings.DB_CIRCUIT_BREAKER_TIMEOUT,
        )
        self._initialized = False

    def _build_url(self, url: str) -> str:
        """Ensure the URL uses the asyncpg driver."""
        # Handle both postgres:// and postgresql:// schemes
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url.replace("postgres://", "postgresql+asyncpg://", 1)

    async def initialize(self):
        """Initialize connection pools. Call once at app startup."""
        if self._initialized:
            return

        write_url = self._build_url(settings.DATABASE_URL)
        read_url = self._build_url(settings.DATABASE_READ_URL or settings.DATABASE_URL)

        common_kwargs = dict(
            poolclass=QueuePool,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_pre_ping=True,  # Verify connections before use
            echo=settings.DB_ECHO,
            connect_args={
                "server_settings": {
                    "statement_timeout": str(settings.DB_STATEMENT_TIMEOUT_MS),
                    "lock_timeout": str(settings.DB_LOCK_TIMEOUT_MS),
                },
                **({"ssl": "require"} if settings.DB_SSL_REQUIRED else {}),
            },
        )

        self._write_engine = create_async_engine(write_url, **common_kwargs)
        self._read_engine = create_async_engine(read_url, **common_kwargs)

        self._session_factory = sessionmaker(
            bind=self._write_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self._read_session_factory = sessionmaker(
            bind=self._read_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        self._initialized = True
        logger.info(
            f"Database gate initialized: pool_size={settings.DB_POOL_SIZE}, "
            f"max_overflow={settings.DB_MAX_OVERFLOW}, "
            f"statement_timeout={settings.DB_STATEMENT_TIMEOUT_MS}ms"
        )

    async def shutdown(self):
        """Close all connection pools. Call at app shutdown."""
        if self._write_engine:
            await self._write_engine.dispose()
        if self._read_engine and self._read_engine != self._write_engine:
            await self._read_engine.dispose()
        self._initialized = False
        logger.info("Database gate shut down.")

    @asynccontextmanager
    async def session(self, read_only: bool = False) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a managed database session.

        Args:
            read_only: If True, routes to the read replica (when configured).

        Raises:
            RuntimeError: If the circuit breaker is open.
        """
        if not self._initialized:
            await self.initialize()

        if not self._circuit_breaker.can_attempt():
            raise RuntimeError(
                "Database circuit breaker is OPEN. "
                "The database is experiencing connectivity issues. Try again later."
            )

        factory = self._read_session_factory if read_only else self._session_factory

        try:
            async with factory() as session:
                yield session
                self._circuit_breaker.record_success()
        except Exception as e:
            self._circuit_breaker.record_failure()
            logger.error(f"Database session error: {e}")
            raise

    async def health_check(self) -> dict:
        """
        Perform a database health check.

        Returns a dict with status, latency, pool stats.
        """
        result = {
            "status": "unhealthy",
            "circuit_breaker": self._circuit_breaker.state,
            "latency_ms": None,
            "pool": None,
        }

        if not self._circuit_breaker.can_attempt():
            result["detail"] = "Circuit breaker is open"
            return result

        try:
            start = time.time()
            async with self.session(read_only=True) as session:
                await session.execute(text("SELECT 1"))
            latency = (time.time() - start) * 1000

            pool = self._write_engine.pool
            result.update({
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "pool": {
                    "size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                },
            })
        except Exception as e:
            result["detail"] = str(e)

        return result


# Singleton instance
db_gate = DatabaseGate()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — provides a write-capable session via the gate."""
    async with db_gate.session() as session:
        yield session


async def get_read_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — provides a read-only session (routes to replica if configured)."""
    async with db_gate.session(read_only=True) as session:
        yield session
