"""Mask member names before sending a rule to the LLM, and restore them afterwards (spec FR-4).

The mapping lives only in memory for one request. It is never stored or logged.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class MaskResult:
    text: str
    mapping: dict[str, str] = field(default_factory=dict)  # token -> original name


def mask_members(text: str, members: list[str], extra_names: list[str] | None = None) -> MaskResult:
    """Replace each member name with a token such as MBR_001.

    `members` usually comes from the parser (quoted names). `extra_names` lets the user
    add unquoted names they also want hidden (e.g. a client entity code).
    """
    names = list(dict.fromkeys([*members, *(extra_names or [])]))
    # Longest names first so "Net Income" is masked before "Income".
    names.sort(key=len, reverse=True)

    mapping: dict[str, str] = {}
    masked = text
    for i, name in enumerate(names, start=1):
        if not name.strip():
            continue
        token = f"MBR_{i:03d}"
        pattern = re.compile(rf"(?<![\w]){re.escape(name)}(?![\w])")
        masked, count = pattern.subn(token, masked)
        if count:
            mapping[token] = name
    return MaskResult(text=masked, mapping=mapping)


def unmask(value, mapping: dict[str, str]):
    """Restore original names in a string, list or dict (works on nested LLM output)."""
    if not mapping:
        return value
    if isinstance(value, str):
        # Replace higher numbers first so MBR_010 isn't broken by MBR_01.
        for token in sorted(mapping, reverse=True):
            value = value.replace(token, mapping[token])
        return value
    if isinstance(value, list):
        return [unmask(v, mapping) for v in value]
    if isinstance(value, dict):
        return {k: unmask(v, mapping) for k, v in value.items()}
    return value
