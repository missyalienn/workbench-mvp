"""
Optional helper for plan_id and structured planner logging.

Reuses config/logging_config setup.
"""

from config.logging_config import get_logger


def get_planner_logger(module_name: str):
    """
    Get a logger for planner modules.

    Wraps config.logging_config.get_logger() for consistency.

    Args:
        module_name: Name of the module requesting the logger

    Returns:
        Logger instance configured via config/logging_config

    TODO: Add optional plan_id context injection if needed
    TODO: Consider structured logging helpers for plan lifecycle events
    """
    return get_logger(module_name)

