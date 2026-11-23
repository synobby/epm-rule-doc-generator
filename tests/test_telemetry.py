import io
import logging

import pytest

from core import telemetry
from core.pipeline import run
from core.validator import ValidationError


@pytest.fixture(autouse=True)
def fresh_stats():
    telemetry.reset()


@pytest.fixture
def log_capture():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    telemetry.logger.addHandler(handler)
    yield stream
    telemetry.logger.removeHandler(handler)


def test_success_is_counted_and_logged(sample, log_capture):
    run(sample("allocate_opex.csc"))
    stats = telemetry.snapshot()
    assert stats["runs"] == 1 and stats["succeeded"] == 1 and stats["calc_scripts"] == 1
    assert '"outcome": "success"' in log_capture.getvalue()


def test_rejected_input_is_counted():
    with pytest.raises(ValidationError):
        run("   ")
    stats = telemetry.snapshot()
    assert stats["rejected_input"] == 1 and stats["succeeded"] == 0


def test_logs_never_contain_rule_text_or_members(sample, log_capture):
    run(sample("allocate_opex.csc"), mask=True)
    log = log_capture.getvalue()
    for secret_ish in ("Corporate_OpEx", "Headcount", "FIX", "Allocated_OpEx"):
        assert secret_ish not in log
