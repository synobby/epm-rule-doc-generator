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
    """Raised when the LLM cannot return a valid answer. `error_type` is logged (no rule text)."""

    def __init__(self, message: str, error_type: str = "llm_error"):
        super().__init__(message)
        self.error_type = error_type


def explain_provider_error(exc: Exception) -> LLMError:
    """Turn an SDK exception (Anthropic, OpenAI, Gemini, Groq) into a clear user message.

    Works by status code / class name, so it needs no provider-specific imports.
    """
    status = getattr(exc, "status_code", None)
    name = type(exc).__name__
    if status == 429 or name == "RateLimitError":
        return LLMError(
            "The AI provider's usage limit was reached (free tiers allow a limited number of "
            "requests per minute and per day). Wait a minute and try again; if it keeps happening, "
            "the daily quota is used up and resets at midnight Pacific time (about 3–4 pm in Manila).",
            "rate_limit",
        )
    if status in (401, 403) or name in ("AuthenticationError", "PermissionDeniedError"):
        return LLMError("The AI provider rejected the API key. Check LLM_API_KEY in the host settings.",
                        "auth")
    if status == 404 or name == "NotFoundError":
        return LLMError("The AI model name was not found. Check LLM_MODEL matches a model ID your "
                        "provider currently offers.", "model_not_found")
    if "Timeout" in name:
        return LLMError("The AI took too long to answer. Try again, or try a shorter rule.", "timeout")
    if "Connection" in name:
        return LLMError("Could not reach the AI provider. Try again in a moment.", "connection")
    if status == 400 or name == "BadRequestError":
        return LLMError("The AI provider rejected the request (bad request). Check LLM_MODEL and the "
                        "provider settings.", "bad_request")
    if status and status >= 500:
        return LLMError("The AI provider had a temporary problem. Try again in a minute.", "provider_down")
    return LLMError("Something went wrong while contacting the AI. Please try again.", name)


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


# Free / low-cost providers that speak the OpenAI API format: only the address differs.
OPENAI_COMPATIBLE = {
    "openai": (None, "gpt-4o-mini"),
    # Flash-Lite: free tier allows far more requests/day than Flash, and it is faster.
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/", "gemini-3.5-flash-lite"),
    "groq": ("https://api.groq.com/openai/v1", "openai/gpt-oss-120b"),
}


class OpenAIProvider:
    """OpenAI, or any OpenAI-compatible service (Gemini, Groq) via base_url."""

    def __init__(self, model: str, api_key: str, timeout: float, base_url: str | None = None):
        import openai

        self.model = model
        # max_retries=1: a quick retry on a blip, without burning a small free-tier quota
        self.client = openai.OpenAI(api_key=api_key, timeout=timeout, base_url=base_url, max_retries=1)

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
    if name in OPENAI_COMPATIBLE:
        default_url, default_model = OPENAI_COMPATIBLE[name]
        base_url = os.getenv("LLM_BASE_URL") or default_url
        return OpenAIProvider(os.getenv("LLM_MODEL", default_model), api_key, timeout, base_url)
    raise LLMError(f"Unknown LLM_PROVIDER '{name}'. Use anthropic, gemini, groq, openai or mock.")


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
        try:
            raw = provider.complete(system, prompt)
        except LLMError:
            raise
        except Exception as exc:  # SDK/network errors -> clear message
            raise explain_provider_error(exc) from exc
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
    raise LLMError(
        "The AI returned an answer in the wrong format twice. Please try again.", "bad_format"
    ) from last_error
