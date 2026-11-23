"""Prompt templates (spec §5.2). Kept in one file so they are easy to read and improve."""

from __future__ import annotations

import json

from core.schemas import DocumentationOutput, RuleFacts, TeachMeOutput

_BASE_RULES = """You are a senior Oracle EPM technical consultant who documents business rules.
Rules you must follow:
- Use ONLY what is in the rule text and the extracted facts. Do not invent members, dimensions or steps.
- The extracted facts were found by code and are correct. Never contradict them.
- If something cannot be known from the rule, write "Not determinable from the rule".
- Tokens like MBR_001 are masked member names. Keep them exactly as written.
- Write in plain, professional English for a consultant audience.
- Reply with a single JSON object only. No markdown, no code fences, no commentary."""

DOCUMENTATION_SYSTEM = (
    _BASE_RULES
    + "\n\nReturn JSON that matches this JSON Schema:\n"
    + json.dumps(DocumentationOutput.model_json_schema())
)

TEACH_ME_SYSTEM = (
    _BASE_RULES
    + "\n\nYou are also a patient teacher for consultants who are new to calc scripts and Groovy."
    + "\nExplain each meaningful line (skip blank lines and pure comment lines)."
    + " In 'concept', name the syntax idea being used (e.g. FIX, cross-dimensional operator, @RELATIVE)."
    + "\n\nReturn JSON that matches this JSON Schema:\n"
    + json.dumps(TeachMeOutput.model_json_schema())
)


def number_lines(text: str) -> str:
    return "\n".join(f"{i:>4} | {line}" for i, line in enumerate(text.split("\n"), start=1))


def build_user_prompt(rule_name: str, rule_text: str, facts: RuleFacts) -> str:
    return (
        f"Rule name: {rule_name}\n"
        f"Rule type: {facts.rule_type}\n\n"
        f"Extracted facts (found by code, treat as correct):\n"
        f"{facts.model_dump_json(indent=2)}\n\n"
        f"Rule text with line numbers:\n{number_lines(rule_text)}"
    )
