"""Extract facts from a Planning Groovy rule (spec §6.3).

Groovy rules often build a calc script as a string and return it. We pull those
embedded calc scripts out and run them through the calc script parser too.
"""

from __future__ import annotations

import re

from core.parser_calc import _unique, parse_calc_script
from core.schemas import RuleFacts

_RTPS_HEADER = re.compile(r"/\*\s*RTPS:\s*(.*?)\*/", re.DOTALL)
_RTPS_USAGE = re.compile(r"\brtps\.(\w+)")
_TRIPLE_QUOTED = re.compile(r'"""(.*?)"""', re.DOTALL)
_API_CALLS = [
    "operation.grid",
    "operation.application",
    "operation.cube",
    "getDataMap",
    "executeDataMap",
    "getSmartPush",
    "execute(",
    "getDimension",
    "getMember",
    "throwVetoException",
    "addMessage",
]


def parse_groovy(text: str) -> RuleFacts:
    rtps: list[str] = []
    header = _RTPS_HEADER.search(text)
    if header:
        rtps += [f"{{{name}}}" for name in re.findall(r"\{\s*(\w+)\s*\}", header.group(1))]
    rtps += [f"rtps.{name}" for name in _RTPS_USAGE.findall(text)]

    api_calls = [call.rstrip("(") for call in _API_CALLS if call in text]

    # Parse any embedded calc script strings ("""FIX(...) ... ENDFIX""").
    fix_blocks, members, functions, commands, warnings = [], [], [], [], []
    for embedded in _TRIPLE_QUOTED.findall(text):
        if re.search(r"\bFIX\s*\(", embedded, re.IGNORECASE):
            facts = parse_calc_script(embedded)
            fix_blocks += facts.fix_blocks
            members += facts.members
            functions += facts.functions
            commands += facts.commands
            warnings += facts.parse_warnings
    if fix_blocks:
        warnings.append(
            "FIX line numbers for embedded calc scripts are relative to the embedded string."
        )

    # Quoted members used directly in Groovy (e.g. getMember("Actual")).
    members += re.findall(r'getMember\(\s*"([^"]+)"', text)

    return RuleFacts(
        rule_type="groovy",
        line_count=len(text.rstrip("\n").split("\n")),
        fix_blocks=fix_blocks,
        members=_unique(members),
        runtime_prompts=_unique(rtps),
        functions=_unique(functions),
        commands=_unique(commands),
        groovy_api_calls=api_calls,
        parse_warnings=warnings,
    )
