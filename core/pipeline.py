"""Runs the full request lifecycle (architecture §4) so the UI stays thin."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from core import llm_client, prompts, telemetry
from core.checks import find_unverified_members
from core.detector import GROOVY, detect_rule_type
from core.masker import mask_members, unmask
from core.parser_calc import parse_calc_script
from core.parser_groovy import parse_groovy
from core.schemas import DocumentationOutput, RuleFacts, TeachMeOutput
from core.validator import ValidationError, validate_rule_text


@dataclass
class PipelineResult:
    facts: RuleFacts
    documentation: DocumentationOutput
    teach_me: TeachMeOutput | None
    warnings: list[str] = field(default_factory=list)
    unverified_members: list[str] = field(default_factory=list)


def parse(text: str, rule_type: str | None = None) -> RuleFacts:
    rule_type = rule_type or detect_rule_type(text)
    return parse_groovy(text) if rule_type == GROOVY else parse_calc_script(text)


def _run(
    raw_text: str | bytes,
    rule_name: str = "Business rule",
    rule_type: str | None = None,
    mask: bool = False,
    extra_mask_names: list[str] | None = None,
    provider: llm_client.Provider | None = None,
) -> PipelineResult:
    # 1-3. Validate, detect, parse (all code, no AI).
    validated = validate_rule_text(raw_text)
    facts = parse(validated.text, rule_type)
    warnings = list(validated.warnings) + facts.parse_warnings

    # 4. Optional masking. The facts sent to the AI are masked too.
    text_for_llm, facts_for_llm, mapping = validated.text, facts, {}
    if mask:
        masked = mask_members(validated.text, facts.members, extra_mask_names)
        text_for_llm, mapping = masked.text, masked.mapping
        facts_for_llm = parse(text_for_llm, facts.rule_type)

    # 5. Two LLM calls in parallel.
    user_prompt = prompts.build_user_prompt(rule_name, text_for_llm, facts_for_llm)
    with ThreadPoolExecutor(max_workers=2) as pool:
        doc_future = pool.submit(
            llm_client.generate, prompts.DOCUMENTATION_SYSTEM, user_prompt, DocumentationOutput, provider
        )
        teach_future = pool.submit(
            llm_client.generate, prompts.TEACH_ME_SYSTEM, user_prompt, TeachMeOutput, provider
        )
        documentation = doc_future.result()  # documentation failing is a real error
        try:
            teach_me = teach_future.result()
        except llm_client.LLMError:
            teach_me = None  # "Teach me" can fail without losing the documentation
            warnings.append("The 'Teach me' view could not be generated this time.")

    # 6-8. Unmask, then cross-check against the original facts.
    if mapping:
        documentation = DocumentationOutput.model_validate(unmask(documentation.model_dump(), mapping))
        if teach_me:
            teach_me = TeachMeOutput.model_validate(unmask(teach_me.model_dump(), mapping))

    return PipelineResult(
        facts=facts,
        documentation=documentation,
        teach_me=teach_me,
        warnings=warnings,
        unverified_members=find_unverified_members(documentation, facts),
    )


def run(
    raw_text: str | bytes,
    rule_name: str = "Business rule",
    rule_type: str | None = None,
    mask: bool = False,
    extra_mask_names: list[str] | None = None,
    provider: llm_client.Provider | None = None,
) -> PipelineResult:
    """Public entry point: runs the pipeline and records one monitoring event (metadata only)."""
    provider = provider or llm_client.get_provider()
    provider_name = type(provider).__name__.removesuffix("Provider").lower()
    with telemetry.Timer() as timer:
        try:
            result = _run(raw_text, rule_name, rule_type, mask, extra_mask_names, provider)
        except ValidationError:
            telemetry.record("rejected_input", timer.elapsed, masked=mask, provider=provider_name)
            raise
        except llm_client.LLMError:
            telemetry.record("ai_error", timer.elapsed, masked=mask, provider=provider_name)
            raise
        except Exception:
            telemetry.record("error", timer.elapsed, masked=mask, provider=provider_name)
            raise
    telemetry.record(
        "success", timer.seconds, result.facts.rule_type, result.facts.line_count, mask, provider_name
    )
    return result

