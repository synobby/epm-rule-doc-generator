"""Detect whether a rule is an Essbase/Planning calc script or a Groovy rule (spec FR-2)."""

from __future__ import annotations

import re

CALC_SCRIPT = "calc_script"
GROOVY = "groovy"

# Strong signals that a rule is Groovy (spec §6.1).
_GROOVY_PATTERNS = [
    r"\boperation\.",
    r"\bdef\s+\w+",
    r"/\*\s*RTPS:",
    r"^\s*import\s+[\w.]+",
    # Groovy closure "{ it ->" -- NOT a bare "->", which is the calc script
    # cross-dimensional operator ("Actual"->"Jan").
    r"\{\s*\w+(\s*,\s*\w+)*\s*->",
    r"\.each\s*\{",
]


def detect_rule_type(text: str) -> str:
    """Return 'groovy' or 'calc_script'."""
    for pattern in _GROOVY_PATTERNS:
        if re.search(pattern, text, flags=re.MULTILINE):
            return GROOVY
    return CALC_SCRIPT
