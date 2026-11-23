import os
import sys
from pathlib import Path

import pytest

# Make "core" importable when running pytest from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Never call a real LLM in tests: no API key, no cost.
os.environ["LLM_PROVIDER"] = "mock"
os.environ.pop("LLM_API_KEY", None)

SAMPLES = Path(__file__).parent / "samples"


@pytest.fixture
def sample():
    def _read(name: str) -> str:
        return (SAMPLES / name).read_text()
    return _read
