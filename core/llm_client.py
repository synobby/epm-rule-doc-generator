"""One small wrapper around the LLM provider (spec §5.1, architecture §5).

Providers:
- "anthropic" : Claude models (default)
- "openai"    : OpenAI models
- "mock"      : no API call; returns a simple answer built from the parser facts.
                Used by the tests and for trying the app without an API key.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Protocol, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

TEMPERATURE = 0.2
MAX_OUTPUT_TOKENS = 8000


class LLMError(RuntimeError):
    """Raised when the LLM cannot return a valid answer."""


class Provider(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class AnthropicProvider:
    def __init__(self, model: str, api_key: str, timeout: float):
        import anthropic

        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key, timeout=timeout)

    def complete(self, system: str, user: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=MAX_OUTPUT_TOKENS,
            temperature=TEMPERATURE,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in response.content if block.type == "text")


class OpenAIProvider:
    def __init__(self, model: str, api_key: str, timeout: float):
        import openai

        self.model = model
        self.client = openai.OpenAI(api_key=api_key, timeout=timeout)

    def complete(self, system: str, user: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=TEMPERATURE,
            max_tokens=MAX_OUTPUT_TOKENS,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        return response.choices[0].message.content or ""


class MockProvider:
    """Builds a placeholder answer from the facts in the prompt. No network, no cost."""

    def complete(self, system: str, user: str) -> str:
        facts = json.loads(user.split("treat as correct):\n", 1)[1].split("\n\nRule text", 1)[0])
        rule_name = user.split("\n", 1)[0].removeprefix("Rule name: ")
        if "patient teacher" in system:
            from core.parser_calc import strip_comments

            numbered = user.split("Rule text with line numbers:\n", 1)[1].split("\n")
            codes = [raw.partition(" | ")[2] for raw in numbered]
            cleaned = strip_comments("\n".join(codes)).split("\n")
            lines = []
            for raw, clean in zip(numbered, cleaned):
                number, _, code = raw.partition(" | ")
                if clean.strip():  # skip blank and comment-only lines
                    lines.append({
                        "line_no": int(number),
                        "code": code,
                        "explanation": "[Demo mode] Explanation appears here when an LLM is connected.",
                        "concept": "",
                    })
            return json.dumps({"lines": lines})
        return json.dumps({
            "rule_name": rule_name,
            "rule_type": facts["rule_type"],
            "purpose": "[Demo mode] Connect an LLM API key to generate the real explanation.",
            "pov_fix_scope": [
                {"dimension": "Not determinable from the rule", "members": b["members"],
                 "source_lines": f"{b['start_line']}-{b['end_line']}"}
                for b in facts["fix_blocks"]
            ],
            "dimensions_and_members": [],
            "runtime_prompts": [{"name": r, "purpose": "Run-time prompt"} for r in facts["runtime_prompts"]],
            "logic_steps": [{"step": i, "description": f"Runs {c}", "source_lines": ""}
                            for i, c in enumerate(facts["commands"], start=1)],
            "risks_and_performance_notes": [],
            "confidence": "low",
        })


def get_provider() -> Provider:
    name = os.getenv("LLM_PROVIDER", "anthropic").lower()
    api_key = os.getenv("LLM_API_KEY", "")
    timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "90"))

    if name == "mock" or not api_key:
        return MockProvider()
    if name == "anthropic":
        return AnthropicProvider(os.getenv("LLM_MODEL", "claude-haiku-5-5"), api_key, timeout)
    if name == "openai":
        return OpenAIProvider(os.getenv("LLM_MODEL", "gpt-4o-mini"), api_key, timeout)
    raise LLMError(f"Unknown LLM_PROVIDER '{name}'. Use anthropic, openai or mock.")


def is_demo_mode() -> bool:
    return isinstance(get_provider(), MockProvider)


def _extract_json(raw: str) -> str:
    """Models sometimes wrap JSON in ```json fences; strip them."""
    raw = raw.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if fenced:
        return fenced.group(1).strip()
    start, end = raw.find("{"), raw.rfind("}")
    return raw[start : end + 1] if start != -1 and end != -1 else raw


_cache: dict[str, BaseModel] = {}


def generate(system: str, user: str, schema: type[T], provider: Provider | None = None) -> T:
    """Call the LLM and validate its JSON against `schema`.

    On invalid JSON, retry once with the validation error appended (spec FR-5).
    Identical requests are served from an in-memory cache (spec NFR-2).
    """
    provider = provider or get_provider()
    key = hashlib.sha256(f"{type(provider).__name__}|{schema.__name__}|{system}|{user}".encode()).hexdigest()
    if key in _cache:
        return _cache[key]  # type: ignore[return-value]

    prompt = user
    last_error: Exception | None = None
    for _attempt in range(2):
        raw = provider.complete(system, prompt)
        try:
            result = schema.model_validate_json(_extract_json(raw))
            _cache[key] = result
            return result
        except ValidationError as exc:
            last_error = exc
            prompt = (
                user
                + "\n\nYour previous answer was not valid JSON for the schema. Error:\n"
                + str(exc)[:1500]
                + "\nReturn only the corrected JSON object."
            )
    raise LLMError("The AI returned an answer in the wrong format twice. Please try again.") from last_error
