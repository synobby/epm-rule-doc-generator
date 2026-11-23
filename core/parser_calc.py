"""Extract facts from an Essbase / Planning calc script with code (spec §6.2).

This is deliberately simple, readable regex work. It does not need to understand
every calc script; it only needs to find the facts we use to ground and check
the AI's explanation.
"""

from __future__ import annotations

import re

from core.schemas import FixBlock, RuleFacts

_FIX_START = re.compile(r"\bFIX\s*\(", re.IGNORECASE)
_ENDFIX = re.compile(r"\bENDFIX\b", re.IGNORECASE)
_QUOTED = re.compile(r'"([^"\n]+)"')
_RTP = re.compile(r"\{\s*([A-Za-z_]\w*)\s*\}")        # Calculation Manager {Variable}
_SUBVAR = re.compile(r"&([A-Za-z_]\w*)")                 # substitution variable
_FUNCTION = re.compile(r"(@[A-Z][A-Z0-9_]*)\s*\(", re.IGNORECASE)
_COMMANDS = [
    ("AGG", re.compile(r"\bAGG\s*\(", re.IGNORECASE)),
    ("CALC DIM", re.compile(r"\bCALC\s+DIM\b", re.IGNORECASE)),
    ("CALC ALL", re.compile(r"\bCALC\s+ALL\b", re.IGNORECASE)),
    ("DATACOPY", re.compile(r"\bDATACOPY\b", re.IGNORECASE)),
    ("CLEARDATA", re.compile(r"\bCLEARDATA\b", re.IGNORECASE)),
    ("CLEARBLOCK", re.compile(r"\bCLEARBLOCK\b", re.IGNORECASE)),
]
_SET = re.compile(r"\bSET\s+([A-Z]+)", re.IGNORECASE)


def strip_comments(text: str) -> str:
    """Remove /* */ and // comments but keep line breaks, so line numbers stay correct."""
    def _blank(match: re.Match) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    text = re.sub(r"/\*.*?\*/", _blank, text, flags=re.DOTALL)
    text = re.sub(r"//[^\n]*", _blank, text)
    return text


def _read_parenthesised(text: str, open_index: int) -> tuple[str, int]:
    """Given the index of '(' return (inside_text, index_after_closing_paren)."""
    depth = 0
    for i in range(open_index, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[open_index + 1 : i], i + 1
    return text[open_index + 1 :], len(text)


def _line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _unique(items: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for item in items:
        seen.setdefault(item, None)
    return list(seen)


def extract_fix_blocks(code: str) -> tuple[list[FixBlock], list[str]]:
    """Walk the script, using a stack to match FIX ... ENDFIX and record nesting depth."""
    events: list[tuple[int, str]] = []
    for m in _FIX_START.finditer(code):
        events.append((m.start(), "FIX"))
    for m in _ENDFIX.finditer(code):
        events.append((m.start(), "ENDFIX"))
    events.sort()

    blocks: list[FixBlock] = []
    stack: list[FixBlock] = []
    warnings: list[str] = []

    for index, kind in events:
        if kind == "FIX":
            paren = code.index("(", index)
            inside, _ = _read_parenthesised(code, paren)
            block = FixBlock(
                members=" ".join(inside.split()),
                depth=len(stack) + 1,
                start_line=_line_of(code, index),
            )
            stack.append(block)
            blocks.append(block)
        else:
            if not stack:
                warnings.append(f"ENDFIX without a matching FIX on line {_line_of(code, index)}.")
                continue
            stack.pop().end_line = _line_of(code, index)

    for block in stack:
        warnings.append(f"FIX on line {block.start_line} has no matching ENDFIX.")

    return blocks, warnings


def parse_calc_script(text: str) -> RuleFacts:
    code = strip_comments(text)
    fix_blocks, warnings = extract_fix_blocks(code)

    commands = [name for name, pattern in _COMMANDS if pattern.search(code)]
    commands += [f"SET {m.upper()}" for m in _SET.findall(code)]

    return RuleFacts(
        rule_type="calc_script",
        line_count=len(text.rstrip("\n").split("\n")),
        fix_blocks=fix_blocks,
        members=_unique(_QUOTED.findall(code)),
        runtime_prompts=_unique(
            [f"{{{v}}}" for v in _RTP.findall(code)] + [f"&{v}" for v in _SUBVAR.findall(code)]
        ),
        functions=_unique([f.upper() for f in _FUNCTION.findall(code)]),
        commands=_unique(commands),
        parse_warnings=warnings,
    )
