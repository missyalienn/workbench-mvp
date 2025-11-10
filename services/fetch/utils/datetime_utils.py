"""Datetime helpers for fetcher modules."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> float:
    """Return the current UTC timestamp as a float."""
    return datetime.now(timezone.utc).timestamp()
