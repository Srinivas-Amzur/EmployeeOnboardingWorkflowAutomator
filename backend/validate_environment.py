#!/usr/bin/env python3
"""Validate runtime database environment for single DATABASE_URL architecture."""

from __future__ import annotations

import asyncio
import socket
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlparse

CHECK_OK = "ok"
CHECK_DNS = "dns issue"
CHECK_NETWORK = "network issue"
CHECK_AUTH = "authentication issue"
CHECK_SSL = "ssl issue"
CHECK_CODE = "code issue"
URL_PREFIX_PG = "postgresql://"
URL_PREFIX_ASYNCPG = "postgresql+asyncpg://"


@dataclass
class CheckResult:
    name: str
    ok: bool
    category: str
    detail: str
    hint: str = ""


def normalize_asyncpg_url(url: str) -> str:
    if url.startswith(URL_PREFIX_PG):
        return url.replace(URL_PREFIX_PG, URL_PREFIX_ASYNCPG, 1)
    return url


def to_asyncpg_dsn(url: str) -> str:
    return normalize_asyncpg_url(url).replace(URL_PREFIX_ASYNCPG, URL_PREFIX_PG, 1)


def classify_error(exc: Exception) -> tuple[str, str]:
    message = str(exc).lower()
    if "ecircuitbreaker" in message or "too many authentication failures" in message:
        return CHECK_AUTH, (
            "Supabase pooler auth lockout triggered by repeated failed logins. "
            "Fix credentials and wait for cooldown before retrying."
        )
    if isinstance(exc, socket.gaierror) or "getaddrinfo failed" in message:
        return CHECK_DNS, "Host resolution failed. Check DNS resolver and IPv6/IPv4 path."
    if isinstance(exc, TimeoutError) or "timeout" in message:
        return CHECK_NETWORK, "Connection timed out. Check firewall, VPN, and network route."
    if isinstance(exc, ConnectionRefusedError) or "connection refused" in message:
        return CHECK_NETWORK, "TCP connection refused. Verify host and port reachability."
    if "password authentication failed" in message or "invalid_password" in message:
        return CHECK_AUTH, (
            "Credentials invalid. Check DATABASE_URL username/password. For pooler use postgres.<project-ref>; "
            "ensure URL has one @ before host and URL-encode special password characters."
        )
    if "ssl" in message or "tls" in message:
        return CHECK_SSL, "SSL negotiation issue. Ensure SSL is enabled and trust chain is valid."
    return CHECK_CODE, "Unhandled runtime error. Check dependencies and stack trace."


def print_result(result: CheckResult) -> None:
    status = "PASS" if result.ok else "FAIL"
    print(f"[{status}] {result.name}")
    print(f"  Category: {result.category}")
    print(f"  Detail:   {result.detail}")
    if result.hint:
        print(f"  Hint:     {result.hint}")


def validate_database_url(database_url: str) -> CheckResult:
    if not database_url:
        return CheckResult(
            name="DATABASE_URL Presence",
            ok=False,
            category=CHECK_CODE,
            detail="DATABASE_URL is missing.",
            hint="Set DATABASE_URL in backend/.env.",
        )

    normalized = normalize_asyncpg_url(database_url)
    parsed = urlparse(normalized)

    if parsed.scheme != "postgresql+asyncpg":
        return CheckResult(
            name="DATABASE_URL Scheme",
            ok=False,
            category=CHECK_CODE,
            detail=f"Invalid scheme: {parsed.scheme}",
            hint="Use postgresql+asyncpg:// (or postgresql:// which is auto-normalized).",
        )

    if not parsed.hostname:
        return CheckResult(
            name="DATABASE_URL Host",
            ok=False,
            category=CHECK_CODE,
            detail="Host is missing.",
            hint="Provide a valid Supabase hostname in DATABASE_URL.",
        )

    if not parsed.path or parsed.path == "/":
        return CheckResult(
            name="DATABASE_URL Database",
            ok=False,
            category=CHECK_CODE,
            detail="Database name is missing.",
            hint="Ensure DATABASE_URL ends with /postgres or your DB name.",
        )

    return CheckResult(
        name="DATABASE_URL Format",
        ok=True,
        category=CHECK_OK,
        detail=f"Host={parsed.hostname}, Port={parsed.port or 5432}, DB={parsed.path.lstrip('/')}",
    )


def check_ssl_flag(database_url: str) -> CheckResult:
    parsed = urlparse(normalize_asyncpg_url(database_url))
    query = parse_qs(parsed.query)
    ssl_mode = (query.get("ssl", [""])[0] or query.get("sslmode", [""])[0]).lower()
    if ssl_mode in {"require", "true", "1", "verify-ca", "verify-full"}:
        return CheckResult(
            name="SSL URL Parameter",
            ok=True,
            category=CHECK_OK,
            detail=f"ssl mode '{ssl_mode}' detected in DATABASE_URL.",
        )
    return CheckResult(
        name="SSL URL Parameter",
        ok=False,
        category=CHECK_SSL,
        detail="No SSL mode parameter found in DATABASE_URL query string.",
        hint="Use DATABASE_URL with ?ssl=require (or ?sslmode=require) for Supabase.",
    )


def check_dns(host: str, port: int) -> CheckResult:
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        ips: list[str] = []
        for info in infos:
            address = info[4][0]
            if address not in ips:
                ips.append(address)
        ipv4 = [ip for ip in ips if ":" not in ip]
        ipv6 = [ip for ip in ips if ":" in ip]
        return CheckResult(
            name="DNS Resolution",
            ok=True,
            category=CHECK_OK,
            detail=f"Resolved {len(ips)} IPs (IPv4={len(ipv4)}, IPv6={len(ipv6)}): {ips}",
        )
    except Exception as exc:  # noqa: BLE001
        category, hint = classify_error(exc)
        return CheckResult(name="DNS Resolution", ok=False, category=category, detail=str(exc), hint=hint)


def check_socket(host: str, port: int, timeout_sec: int) -> CheckResult:
    started = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout_sec):
            latency_ms = round((time.perf_counter() - started) * 1000, 2)
            return CheckResult(
                name="TCP Reachability",
                ok=True,
                category=CHECK_OK,
                detail=f"Connected to {host}:{port} in {latency_ms} ms",
            )
    except Exception as exc:  # noqa: BLE001
        category, hint = classify_error(exc)
        return CheckResult(name="TCP Reachability", ok=False, category=category, detail=str(exc), hint=hint)


async def check_asyncpg(database_url: str, require_ssl: bool, timeout_sec: int, command_timeout: int) -> CheckResult:
    try:
        import asyncpg
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            name="asyncpg Availability",
            ok=False,
            category=CHECK_CODE,
            detail=str(exc),
            hint="Install dependencies: pip install -r requirements.txt",
        )

    connect_kwargs: dict[str, Any] = {
        "dsn": to_asyncpg_dsn(database_url),
        "timeout": timeout_sec,
        "command_timeout": command_timeout,
    }
    if require_ssl:
        connect_kwargs["ssl"] = "require"

    started = time.perf_counter()
    try:
        conn = await asyncpg.connect(**connect_kwargs)
        version = await conn.fetchval("SELECT version()")
        await conn.close()
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        return CheckResult(
            name="asyncpg Connectivity",
            ok=True,
            category=CHECK_OK,
            detail=f"Connected in {latency_ms} ms. Version={str(version)[:80]}",
        )
    except Exception as exc:  # noqa: BLE001
        category, hint = classify_error(exc)
        return CheckResult(name="asyncpg Connectivity", ok=False, category=category, detail=str(exc), hint=hint)


def infer_mode(host: str) -> str:
    if host.endswith(".pooler.supabase.com"):
        return "pooler"
    if host.endswith((".supabase.co", ".supabase.com")):
        return "direct"
    return "custom"


async def main() -> int:
    print("=" * 72)
    print("Environment Validation (Single DATABASE_URL)")
    print("=" * 72)

    try:
        from app.core.config import get_settings

        settings = get_settings()
        settings.validate_database_url()
    except Exception as exc:  # noqa: BLE001
        print_result(
            CheckResult(
                name="Settings Validation",
                ok=False,
                category=CHECK_CODE,
                detail=str(exc),
                hint="Fix DATABASE_URL and rerun validate_environment.py",
            )
        )
        return 2

    database_url = settings.resolved_database_url()
    parsed = urlparse(database_url)
    host = parsed.hostname or "unknown"
    port = parsed.port or 5432
    mode = infer_mode(host)

    print(f"Active mode inferred from DATABASE_URL host: {mode}")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"DB_SSL_REQUIRE setting: {settings.DB_SSL_REQUIRE}")
    print()

    results: list[CheckResult] = [
        validate_database_url(database_url),
        check_ssl_flag(database_url),
        check_dns(host, port),
        check_socket(host, port, settings.DB_SOCKET_TIMEOUT),
        await check_asyncpg(
            database_url=database_url,
            require_ssl=settings.DB_SSL_REQUIRE,
            timeout_sec=settings.DB_CONNECT_TIMEOUT,
            command_timeout=settings.DB_COMMAND_TIMEOUT,
        ),
    ]

    for result in results:
        print_result(result)

    failed = [result for result in results if not result.ok]
    print("\nSummary")
    print("-" * 72)
    print(f"Passed: {len(results) - len(failed)}/{len(results)}")

    if not failed:
        print("Overall: Supabase-only DATABASE_URL configuration is healthy.")
        return 0

    categories = sorted({result.category for result in failed})
    print(f"Overall: Issues detected ({', '.join(categories)}).")
    for result in failed:
        print(f"- {result.name}: {result.category} -> {result.hint or result.detail}")

    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
