"""Basic monitoring (assignment Phase 4).

Every generation writes ONE JSON line to the app log (visible in the Render "Logs" tab)
and updates in-memory counters shown in the app's sidebar.

Privacy: only metadata is recorded -- never rule text, member names or API keys.
"""

from __future__ import annotations

import json
import logging
import sys
import threading
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

logger = logging.getLogger("epm_rule_doc")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

_lock = threading.Lock()


@dataclass
class UsageStats:
    runs: int = 0
    succeeded: int = 0
    rejected_input: int = 0
    ai_errors: int = 0
    total_seconds: float = 0.0
    calc_scripts: int = 0
    groovy_rules: int = 0

    @property
    def avg_seconds(self) -> float:
        return self.total_seconds / self.succeeded if self.succeeded else 0.0

    @property
    def success_rate(self) -> float:
        return self.succeeded / self.runs if self.runs else 0.0


_stats = UsageStats()


def record(
    outcome: str,
    duration_s: float,
    rule_type: str | None = None,
    line_count: int | None = None,
    masked: bool = False,
    provider: str | None = None,
) -> dict:
    """Log one generation event. outcome: 'success' | 'rejected_input' | 'ai_error' | 'error'."""
    event = {
        "event": "generate",
        "ts": datetime.now(UTC).isoformat(timespec="seconds"),
        "outcome": outcome,
        "duration_s": round(duration_s, 2),
        "rule_type": rule_type,
        "line_count": line_count,
        "masked": masked,
        "provider": provider,
    }
    logger.info(json.dumps(event))

    with _lock:
        _stats.runs += 1
        if outcome == "success":
            _stats.succeeded += 1
            _stats.total_seconds += duration_s
            if rule_type == "groovy":
                _stats.groovy_rules += 1
            elif rule_type == "calc_script":
                _stats.calc_scripts += 1
        elif outcome == "rejected_input":
            _stats.rejected_input += 1
        else:
            _stats.ai_errors += 1
    return event


def snapshot() -> dict:
    """Copy of the counters since the app last started."""
    with _lock:
        data = asdict(_stats)
        data["avg_seconds"] = round(_stats.avg_seconds, 2)
        data["success_rate"] = round(_stats.success_rate, 3)
    return data


def reset() -> None:
    """For tests."""
    global _stats
    with _lock:
        _stats = UsageStats()


class Timer:
    """with Timer() as t: ...  then t.seconds"""

    def __enter__(self):
        self._start = time.perf_counter()
        self.seconds = 0.0
        return self

    @property
    def elapsed(self) -> float:
        """Seconds so far (usable inside the `with` block)."""
        return time.perf_counter() - self._start

    def __exit__(self, *exc):
        self.seconds = time.perf_counter() - self._start
        return False
