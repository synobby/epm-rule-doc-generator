"""Cross-check the AI's documentation against the parser facts (spec §5.5)."""

from __future__ import annotations

import re

from core.schemas import DocumentationOutput, RuleFacts


def find_unverified_members(doc: DocumentationOutput, facts: RuleFacts) -> list[str]:
    """Return member names the AI put in the FIX scope that the parser did not find.

    Only quoted names are checked (e.g. "Actual"), because the parser only extracts
    quoted members. An empty list means nothing suspicious was found.
    """
    known = {m.lower() for m in facts.members}
    fix_text = " ".join(b.members for b in facts.fix_blocks).lower()

    suspicious: list[str] = []
    for item in doc.pov_fix_scope:
        for name in re.findall(r'"([^"]+)"', item.members):
            if name.lower() not in known and name.lower() not in fix_text:
                suspicious.append(name)
    return list(dict.fromkeys(suspicious))
