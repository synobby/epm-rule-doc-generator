"""Data models.

- RuleFacts: what the parser finds with code (no AI).
- DocumentationOutput / TeachMeOutput: the JSON the LLM must return (spec §5.3, §5.4).
Pydantic validates the LLM's JSON so a malformed answer is caught, not shown.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ---------- Parser output (code, not AI) ----------

class FixBlock(BaseModel):
    members: str = Field(description="Raw text inside FIX( ... )")
    depth: int = Field(description="1 = outermost FIX")
    start_line: int
    end_line: int | None = None


class RuleFacts(BaseModel):
    rule_type: Literal["calc_script", "groovy"]
    line_count: int
    fix_blocks: list[FixBlock] = []
    members: list[str] = []
    runtime_prompts: list[str] = []
    functions: list[str] = []
    commands: list[str] = []
    groovy_api_calls: list[str] = []
    parse_warnings: list[str] = []


# ---------- LLM output: documentation ----------

class ScopeItem(BaseModel):
    dimension: str
    members: str
    source_lines: str = ""


class DimensionUsage(BaseModel):
    dimension: str
    members_read: str = ""
    members_written: str = ""


class RuntimePrompt(BaseModel):
    name: str
    purpose: str


class LogicStep(BaseModel):
    step: int
    description: str
    source_lines: str = ""


class RiskNote(BaseModel):
    severity: Literal["high", "medium", "low"]
    note: str


class DocumentationOutput(BaseModel):
    rule_name: str
    rule_type: Literal["calc_script", "groovy"]
    purpose: str
    pov_fix_scope: list[ScopeItem] = []
    dimensions_and_members: list[DimensionUsage] = []
    runtime_prompts: list[RuntimePrompt] = []
    logic_steps: list[LogicStep] = []
    risks_and_performance_notes: list[RiskNote] = []
    confidence: Literal["high", "medium", "low"] = "medium"


# ---------- LLM output: "Teach me" ----------

class TeachLine(BaseModel):
    line_no: int
    code: str
    explanation: str
    concept: str = ""


class TeachMeOutput(BaseModel):
    lines: list[TeachLine] = []
