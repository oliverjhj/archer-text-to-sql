"""
Unit tests for the daily question budget in archer.core.usage.

Why this is tested carefully
----------------------------
This is the only hard cost ceiling the system has. IBM Cloud's spending
controls are notifications, not limits: they email when money has already been
spent and stop nothing. If this counter is wrong, the failure mode is a bill
rather than an error, and nothing else in the stack will catch it.

Every test constructs its own budget rather than using the module-level one, so
they cannot influence each other or leak state into the rest of the suite.
"""

import pytest

from datetime import date
from unittest.mock import patch

from archer.core.usage import DEFAULT_DAILY_LIMIT, DailyQuestionBudget


@pytest.mark.unit
def test_allows_questions_up_to_the_limit() -> None:
    budget = DailyQuestionBudget()
    with patch.dict("os.environ", {"DEMO_DAILY_QUESTION_LIMIT": "3"}):
        assert [budget.try_consume() for _ in range(3)] == [True, True, True]


@pytest.mark.unit
def test_refuses_past_the_limit() -> None:
    """The whole point: the next question after the limit is refused."""
    budget = DailyQuestionBudget()
    with patch.dict("os.environ", {"DEMO_DAILY_QUESTION_LIMIT": "2"}):
        budget.try_consume()
        budget.try_consume()
        assert budget.try_consume() is False
        assert budget.try_consume() is False


@pytest.mark.unit
def test_counter_resets_on_a_new_day() -> None:
    """
    A budget that never resets would take the demo offline permanently after
    one busy day, which is a worse failure than the one it prevents.
    """
    budget = DailyQuestionBudget()
    with patch.dict("os.environ", {"DEMO_DAILY_QUESTION_LIMIT": "1"}):
        assert budget.try_consume(date(2026, 9, 1)) is True
        assert budget.try_consume(date(2026, 9, 1)) is False
        assert budget.try_consume(date(2026, 9, 2)) is True


@pytest.mark.unit
def test_zero_or_negative_limit_disables_the_ceiling() -> None:
    """
    Local development and the evaluation suite need to run unmetered. Neither
    is exposed to the internet, so an explicit opt-out is safe - and better
    than the alternative of people commenting the check out.
    """
    budget = DailyQuestionBudget()
    with patch.dict("os.environ", {"DEMO_DAILY_QUESTION_LIMIT": "0"}):
        assert all(budget.try_consume() for _ in range(50))


@pytest.mark.unit
def test_unset_limit_falls_back_to_the_default() -> None:
    """A missing variable must not mean unlimited spending."""
    budget = DailyQuestionBudget()
    with patch.dict("os.environ", {}, clear=False):
        import os

        os.environ.pop("DEMO_DAILY_QUESTION_LIMIT", None)
        assert budget.try_consume() is True
        assert budget.snapshot()["limit"] == DEFAULT_DAILY_LIMIT


@pytest.mark.unit
def test_malformed_limit_falls_back_to_the_default() -> None:
    """
    A typo in configuration must not disable the ceiling. Failing open here
    would be the expensive direction to fail in.
    """
    budget = DailyQuestionBudget()
    with patch.dict("os.environ", {"DEMO_DAILY_QUESTION_LIMIT": "not-a-number"}):
        assert budget.try_consume() is True
        assert budget.snapshot()["limit"] == DEFAULT_DAILY_LIMIT


@pytest.mark.unit
def test_snapshot_reports_usage() -> None:
    budget = DailyQuestionBudget()
    with patch.dict("os.environ", {"DEMO_DAILY_QUESTION_LIMIT": "10"}):
        budget.try_consume(date(2026, 9, 1))
        budget.try_consume(date(2026, 9, 1))
        snapshot = budget.snapshot()

    assert snapshot["used"] == 2
    assert snapshot["day"] == "2026-09-01"


@pytest.mark.unit
def test_counting_is_thread_safe() -> None:
    """
    The budget is consumed from worker threads, because the model call is
    moved off the event loop with asyncio.to_thread. An unsynchronised
    increment would undercount under exactly the load that matters.
    """
    import threading

    budget = DailyQuestionBudget()
    granted = []
    lock = threading.Lock()

    def worker() -> None:
        allowed = budget.try_consume(date(2026, 9, 1))
        with lock:
            granted.append(allowed)

    with patch.dict("os.environ", {"DEMO_DAILY_QUESTION_LIMIT": "25"}):
        threads = [threading.Thread(target=worker) for _ in range(100)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    assert sum(granted) == 25, "exactly the limit should have been granted"
