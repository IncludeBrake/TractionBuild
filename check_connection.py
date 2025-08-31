"""Compatibility shim providing Neo4j connection helpers expected by older tests.
It proxies to internal ZerotoShip utilities if available, or provides a lightweight
fallback so the test suite can run even when Neo4j is not running.
"""

from __future__ import annotations

import os
import asyncio
from typing import Any, Dict

# Attempt to import the official async neo4j driver. If unavailable, treat Neo4j as absent.
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:  # pragma: no cover – optional dependency
    NEO4J_AVAILABLE = False

__all__ = [
    "check_connection",
    "get_connection_info",
    "health_check",
]

DEFAULT_TIMEOUT = 3  # seconds


async def _attempt_connect(timeout: int = DEFAULT_TIMEOUT) -> bool:
    """Try to establish a Neo4j connection quickly.

    Returns True on success, False on any exception or when the driver
    isn't available.
    """
    if not NEO4J_AVAILABLE:
        return False

    uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "neo4j")

    loop = asyncio.get_running_loop()

    def _connect_sync() -> bool:
        try:
            drv = GraphDatabase.driver(uri, auth=(user, password))
            drv.verify_connectivity()
            drv.close()
            return True
        except Exception:
            return False

    try:
        return await asyncio.wait_for(loop.run_in_executor(None, _connect_sync), timeout=timeout)
    except asyncio.TimeoutError:
        return False


async def check_connection(timeout: int = DEFAULT_TIMEOUT) -> bool:  # noqa: D401
    """Return True if a Neo4j connection can be established within *timeout* seconds."""
    return await _attempt_connect(timeout)


async def get_connection_info(timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """Return a dictionary describing the current Neo4j connection settings and viability."""
    uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password_set = bool(os.getenv("NEO4J_PASSWORD"))

    info: Dict[str, Any] = {
        "uri": uri,
        "user": user,
        "password_set": password_set,
        "pool_size": 1,  # minimal placeholder – would be driver.config.max_connection_pool_size
        "timeout": timeout,
        "retry_attempts": 0,
        "prometheus_available": False,
        "opentelemetry_available": False,
    }

    # Quick connectivity probe
    info["connection_success"] = await _attempt_connect(timeout)
    return info


async def health_check(timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """Return a simple health report comparable to FastAPI health-check endpoint."""
    ok = await _attempt_connect(timeout)
    report: Dict[str, Any] = {
        "status": "healthy" if ok else "error",
        "connection_success": ok,
    }

    # Attempt a trivial query if connected
    if ok and NEO4J_AVAILABLE:
        uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "neo4j")
        try:
            drv = GraphDatabase.driver(uri, auth=(user, password))
            with drv.session() as s:
                s.run("RETURN 1 AS result").single()
            drv.close()
            report["query_success"] = True
        except Exception as e:  # pragma: no cover – connection lost after verify
            report["query_success"] = False
            report["error"] = str(e)
    else:
        report["query_success"] = False

    return report