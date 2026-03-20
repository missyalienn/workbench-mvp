"""Run context helpers for observability.

Summary:
    Provides run_id generation, query sanitization, and timing helpers for
    consistent logging across pipeline stages.

Usage:
    from services.observability.run_context import generate_run_id, sanitize_query, elapsed_ms

    run_id = generate_run_id()
    safe_query = sanitize_query(user_query)
    start = time.perf_counter()
    duration_ms = elapsed_ms(start)
"""

from __future__ import annotations

import time
from uuid import uuid4


def generate_run_id() -> str:
    """Return a new run identifier."""
    return uuid4().hex


def sanitize_query(query: str, max_len: int = 120) -> str:
    """Return a normalized, truncated query preview for logs."""
    cleaned = " ".join((query or "").strip().split())
    if len(cleaned) <= max_len:
        return cleaned
    return f"{cleaned[:max_len]}…"


def elapsed_ms(start_time: float) -> int:
    """Return elapsed milliseconds since start_time."""
    return int((time.perf_counter() - start_time) * 1000)

