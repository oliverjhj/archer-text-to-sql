"""
A daily ceiling on how many questions the demo will answer.

Why this is in the application
------------------------------
IBM Cloud has no hard spending limit. Spending notifications are exactly that -
an email at 80%, 90% and 100% of a threshold - and nothing stops. For a public
demo sitting in front of a paid model that is not a control, it is a warning
that money has already gone.

So the ceiling lives here, where it can actually refuse. Per-IP rate limiting
(slowapi, on the routes) stops one visitor hammering the service; this stops
the aggregate, which is the part that costs money.

What it does not do
-------------------
The counter is per process. The application runs at maximum scale 2, so the
true worst case is twice the configured limit. Sharing a counter across
instances would mean running Redis - another service, another failure mode, and
another thing to pay for - to make a demo's cost ceiling exact rather than
approximate. Two times a small number is still a small number, so the
approximation is the right trade and is stated rather than hidden.

The limit resets at midnight UTC. It is deliberately not persisted: a restart
clearing the count is acceptable, because a container that restarts often
enough to matter is a different problem.
"""

from __future__ import annotations

import logging
import os
import threading
from datetime import date

DEFAULT_DAILY_LIMIT = 200


def _configured_limit() -> int:
    """
    Read the limit from the environment.

    A value of 0 or below disables the ceiling, which is what local development
    and the evaluation suite want; neither is exposed to the internet.
    """
    raw = os.environ.get("DEMO_DAILY_QUESTION_LIMIT", "").strip()
    if not raw:
        return DEFAULT_DAILY_LIMIT
    try:
        return int(raw)
    except ValueError:
        logging.warning(
            "DEMO_DAILY_QUESTION_LIMIT=%r is not an integer; using default %d",
            raw,
            DEFAULT_DAILY_LIMIT,
        )
        return DEFAULT_DAILY_LIMIT


class DailyQuestionBudget:
    """Counts questions answered today and refuses once the limit is reached."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._day: date | None = None
        self._count = 0

    def _roll(self, today: date) -> None:
        """Reset the counter when the day changes. Caller holds the lock."""
        if self._day != today:
            if self._day is not None:
                logging.info(
                    "Daily question budget reset: %d answered on %s", self._count, self._day
                )
            self._day = today
            self._count = 0

    def try_consume(self, today: date | None = None) -> bool:
        """
        Claim one question against today's budget.

        Returns True if the question may proceed. The claim happens before the
        model is called, not after, because the cost is incurred by asking.
        """
        limit = _configured_limit()
        if limit <= 0:
            return True

        with self._lock:
            self._roll(today or date.today())
            if self._count >= limit:
                return False
            self._count += 1
            if self._count == limit:
                logging.warning(
                    "Daily question budget of %d reached; further questions will be refused today",
                    limit,
                )
            return True

    def snapshot(self) -> dict:
        """Current state, for logging and diagnostics."""
        with self._lock:
            return {"day": str(self._day), "used": self._count, "limit": _configured_limit()}


# One budget per process, matching the scope of the counter.
budget = DailyQuestionBudget()

BUDGET_EXHAUSTED_MESSAGE = (
    "This demo has reached its daily question limit, which keeps its running "
    "costs predictable. It resets at midnight UTC - please try again tomorrow."
)
