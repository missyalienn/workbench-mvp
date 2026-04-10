"""Unit tests for agent.planner.errors."""

from __future__ import annotations

from agent.planner.errors import PlannerError


def test_planner_error_message() -> None:
    err = PlannerError("something failed")
    assert str(err) == "something failed"


def test_planner_error_is_not_runtime_error() -> None:
    """Regression guard — PlannerError replaced RuntimeError; must not be the same type."""
    err = PlannerError("something failed")
    assert not isinstance(err, RuntimeError)


def test_planner_error_stores_cause() -> None:
    cause = ValueError("original")
    err = PlannerError("wrapped", cause=cause)
    assert err.cause is cause


def test_planner_error_stores_details() -> None:
    err = PlannerError("wrapped", details={"model": "gpt-4.1-mini"})
    assert err.details == {"model": "gpt-4.1-mini"}
