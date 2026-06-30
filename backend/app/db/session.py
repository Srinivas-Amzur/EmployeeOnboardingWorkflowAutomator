"""
Database connection and session management.
"""

import asyncio
import logging
import socket
import time
from typing import Any
from typing import AsyncGenerator
from urllib.parse import urlparse
from uuid import uuid4

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from ..core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)
SQL_PING_QUERY = "SELECT 1"
SQL_PING_TEXT = text(SQL_PING_QUERY)

try:
    settings.validate_database_url()
except ValueError as exc:
    raise RuntimeError(f"DATABASE_URL is invalid: {exc}") from exc

DATABASE_URL = settings.resolved_database_url()


def _to_asyncpg_dsn(sqlalchemy_url: str) -> str:
    return sqlalchemy_url.replace("postgresql+asyncpg://", "postgresql://", 1)


def _db_target() -> tuple[str, int, str]:
    parsed = urlparse(DATABASE_URL)
    return (
        parsed.hostname or "unknown",
        parsed.port or 5432,
        parsed.path.lstrip("/") or "postgres",
    )


def _classify_connection_error(exc: Exception) -> dict[str, str]:
    message = str(exc).lower()

    if "ecircuitbreaker" in message or "too many authentication failures" in message:
        return {
            "category": "auth_lockout",
            "hint": "Supabase pooler temporarily blocked auth attempts after repeated failures. Fix credentials, then wait for lockout cooldown before retrying.",
        }

    if isinstance(exc, socket.gaierror) or "getaddrinfo failed" in message:
        return {
            "category": "dns",
            "hint": "Probable DNS/resolver issue (often IPv6 path on Windows).",
        }
    if isinstance(exc, TimeoutError) or "timeout" in message:
        return {
            "category": "timeout",
            "hint": "Connection timed out. Check firewall, VPN, route, and endpoint reachability.",
        }
    if isinstance(exc, ConnectionRefusedError) or "connection refused" in message:
        return {
            "category": "network",
            "hint": "TCP connection refused. Check host/port and remote endpoint availability.",
        }
    if "password authentication failed" in message or "invalid_password" in message:
        return {
            "category": "auth",
            "hint": "Invalid DB credentials in DATABASE_URL. For pooler use postgres.<project-ref>; also verify URL format (single @ before host) and URL-encode special password characters.",
        }
    if "ssl" in message or "tls" in message:
        return {
            "category": "ssl",
            "hint": "SSL negotiation/certificate issue. Ensure SSL is enabled and trust chain is valid.",
        }
    return {
        "category": "unknown",
        "hint": "Unhandled DB connectivity error. Inspect logs and endpoint settings.",
    }


def _resolve_ips(host: str, port: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": False,
        "addresses": [],
        "ipv4": [],
        "ipv6": [],
        "error": None,
    }
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        addresses: list[str] = []
        for info in infos:
            ip = info[4][0]
            if ip not in addresses:
                addresses.append(ip)
        result["addresses"] = addresses
        result["ipv4"] = [ip for ip in addresses if ":" not in ip]
        result["ipv6"] = [ip for ip in addresses if ":" in ip]
        result["ok"] = True
        return result
    except Exception as exc:  # noqa: BLE001
        result["error"] = str(exc)
        return result


def _socket_test(host: str, port: int, timeout_sec: int) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout_sec):
            return {
                "ok": True,
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "error": None,
            }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "latency_ms": None,
            "error": str(exc),
        }


async def _asyncpg_test() -> dict[str, Any]:
    host, port, database = _db_target()
    started = time.perf_counter()
    try:
        connect_kwargs: dict[str, Any] = {
            "dsn": _to_asyncpg_dsn(DATABASE_URL),
            "timeout": settings.DB_CONNECT_TIMEOUT,
            "command_timeout": settings.DB_COMMAND_TIMEOUT,
        }
        if settings.using_supabase() and settings.DB_SSL_REQUIRE:
            connect_kwargs["ssl"] = "require"
            # Supabase poolers run PgBouncer in transaction mode.
            # Disable statement cache to avoid invalid prepared statement errors.
            connect_kwargs["statement_cache_size"] = 0

        conn = await asyncpg.connect(**connect_kwargs)
        await conn.fetchval(SQL_PING_QUERY)
        version = await conn.fetchval("SELECT version()")
        await conn.close()
        return {
            "ok": True,
            "host": host,
            "port": port,
            "database": database,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "version": str(version),
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        classified = _classify_connection_error(exc)
        return {
            "ok": False,
            "host": host,
            "port": port,
            "database": database,
            "latency_ms": None,
            "version": None,
            "error": str(exc),
            "category": classified["category"],
            "hint": classified["hint"],
        }


async def collect_db_diagnostics() -> dict[str, Any]:
    host, port, database = _db_target()
    return {
        "target": {
            "host": host,
            "port": port,
            "database": database,
            "mode": "single-database-url",
            "ssl_enabled": bool(settings.using_supabase() and settings.DB_SSL_REQUIRE),
            "using_supabase": settings.using_supabase(),
        },
        "resolver": _resolve_ips(host, port),
        "socket": _socket_test(host, port, settings.DB_SOCKET_TIMEOUT),
        "asyncpg": await _asyncpg_test(),
    }


async def log_startup_db_diagnostics() -> None:
    diagnostics = await collect_db_diagnostics()
    target = diagnostics["target"]
    resolver = diagnostics["resolver"]
    socket_result = diagnostics["socket"]
    asyncpg_result = diagnostics["asyncpg"]

    logger.info(
        "DB startup host=%s port=%s database=%s ssl_enabled=%s mode=%s",
        target["host"],
        target["port"],
        target["database"],
        target["ssl_enabled"],
        target["mode"],
    )

    if resolver["ok"]:
        logger.info(
            "DB resolver addresses=%s ipv4=%d ipv6=%d",
            resolver["addresses"],
            len(resolver["ipv4"]),
            len(resolver["ipv6"]),
        )
    else:
        logger.error("DB resolver failed: %s", resolver["error"])

    if socket_result["ok"]:
        logger.info("DB socket connectivity latency_ms=%.2f", socket_result["latency_ms"])
    else:
        logger.error("DB socket connectivity failed: %s", socket_result["error"])

    if asyncpg_result["ok"]:
        logger.info("DB asyncpg connectivity latency_ms=%.2f", asyncpg_result["latency_ms"])
    else:
        logger.error(
            "DB asyncpg connectivity failed [%s]: %s. %s",
            asyncpg_result.get("category", "unknown"),
            asyncpg_result.get("error"),
            asyncpg_result.get("hint", ""),
        )


async def retry_warmup_connection(attempt: int = 0, max_retries: int = 5) -> bool:
    if attempt > max_retries:
        return False

    try:
        async with engine.connect() as conn:
            await conn.execute(SQL_PING_TEXT)
        return True
    except Exception as exc:  # noqa: BLE001
        classified = _classify_connection_error(exc)

        if classified["category"] in {"auth", "auth_lockout"}:
            logger.exception(
                "DB warm-up aborted [%s]: %s. %s",
                classified["category"],
                exc,
                classified["hint"],
            )
            return False

        wait_time = min(2 ** attempt, 10)
        logger.warning(
            "DB warm-up attempt %d/%d failed [%s]: %s. %s Retrying in %ds...",
            attempt + 1,
            max_retries + 1,
            classified["category"],
            exc,
            classified["hint"],
            wait_time,
        )
        await asyncio.sleep(wait_time)
        return await retry_warmup_connection(attempt + 1, max_retries)

# Create async engine
engine_connect_args: dict[str, Any] = {
    "timeout": settings.DB_CONNECT_TIMEOUT,
    "command_timeout": settings.DB_COMMAND_TIMEOUT,
}
if settings.using_supabase() and settings.DB_SSL_REQUIRE:
    engine_connect_args["ssl"] = "require"
    # Supabase poolers run PgBouncer in transaction mode.
    # Disable statement cache to avoid invalid prepared statement errors.
    engine_connect_args["statement_cache_size"] = 0
    engine_connect_args["prepared_statement_cache_size"] = 0
    engine_connect_args["prepared_statement_name_func"] = lambda: f"__asyncpg_{uuid4()}__"

engine_kwargs: dict[str, Any] = {
    "echo": settings.DEBUG,
    "future": True,
    "pool_pre_ping": True,
    "pool_size": settings.DB_POOL_SIZE,
    "max_overflow": settings.DB_MAX_OVERFLOW,
    # Recycle connections after 10 min to avoid stale/network-reset connections
    "pool_recycle": settings.DB_POOL_RECYCLE,
    "pool_timeout": settings.DB_POOL_TIMEOUT,
    "connect_args": engine_connect_args,
}

if settings.using_supabase():
    # With Supabase PgBouncer, NullPool avoids prepared statement conflicts.
    # Rely on external pooling rather than SQLAlchemy connection pooling.
    engine_kwargs["poolclass"] = NullPool
    engine_kwargs.pop("pool_size", None)
    engine_kwargs.pop("max_overflow", None)
    engine_kwargs.pop("pool_timeout", None)
    engine_kwargs.pop("pool_recycle", None)

engine = create_async_engine(DATABASE_URL, **engine_kwargs)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.

    Yields:
        AsyncSession instance
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_db_health() -> dict[str, Any]:
    diagnostics = await collect_db_diagnostics()
    target = diagnostics["target"]
    asyncpg_result = diagnostics["asyncpg"]

    payload: dict[str, Any] = {
        "connected": bool(asyncpg_result.get("ok")),
        "latency_ms": asyncpg_result.get("latency_ms"),
        "host": target["host"],
        "port": target["port"],
        "database": target["database"],
        "ssl_enabled": target["ssl_enabled"],
        "mode": target["mode"],
        "database_version": asyncpg_result.get("version"),
        "resolver": diagnostics["resolver"],
    }

    if not payload["connected"]:
        payload["error"] = asyncpg_result.get("error")
        payload["error_category"] = asyncpg_result.get("category")
        payload["error_hint"] = asyncpg_result.get("hint")

    return payload
