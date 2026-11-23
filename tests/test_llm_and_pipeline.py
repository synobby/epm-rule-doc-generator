import io

import pytest
from docx import Document

from core import llm_client
from core.exporters import safe_filename, to_docx, to_markdown
from core.pipeline import run
from core.schemas import DocumentationOutput, TeachMeOutput

VALID_DOC = DocumentationOutput(rule_name="R", rule_type="calc_script", purpose="p").model_dump_json()


class ScriptedProvider:
    """Returns pre-set answers in order, so we can test retries without a real LLM."""

    def __init__(self, answers):
        self.answers = list(answers)
        self.calls = 0

    def complete(self, system, user):
        self.calls += 1
        return self.answers.pop(0)


@pytest.fixture(autouse=True)
def clear_cache():
    llm_client._cache.clear()


def test_retry_once_then_succeed():
    provider = ScriptedProvider(["not json", VALID_DOC])
    result = llm_client.generate("sys", "user", DocumentationOutput, provider)
    assert result.rule_name == "R" and provider.calls == 2


def test_fails_after_two_bad_answers():
    provider = ScriptedProvider(["bad", "still bad"])
    with pytest.raises(llm_client.LLMError):
        llm_client.generate("sys", "user", DocumentationOutput, provider)


def test_code_fences_are_stripped():
    provider = ScriptedProvider([f"```json\n{VALID_DOC}\n```"])
    assert llm_client.generate("s", "u", DocumentationOutput, provider).purpose == "p"


def test_full_pipeline_in_mock_mode(sample):
    result = run(sample("allocate_opex.csc"), rule_name="Allocate OpEx")
    assert result.facts.rule_type == "calc_script"
    assert len(result.documentation.pov_fix_scope) == 2
    assert isinstance(result.teach_me, TeachMeOutput)
    assert result.teach_me.lines and result.teach_me.lines[0].line_no >= 3  # comments skipped
    assert result.unverified_members == []


def test_pipeline_with_masking_restores_names(sample):
    result = run(sample("allocate_opex.csc"), mask=True)
    scope_text = " ".join(s.members for s in result.documentation.pov_fix_scope)
    assert "MBR_" not in scope_text and "Total_BU" in scope_text


def test_exporters_include_all_sections(sample):
    doc = run(sample("copy_actuals.csc"), rule_name="Copy Actuals").documentation
    md = to_markdown(doc)
    for heading in ("Purpose", "POV / FIX scope", "Dimensions and members", "Run-time prompts",
                    "Step-by-step logic", "Risks and performance notes", "review required"):
        assert heading in md
    text = "\n".join(p.text for p in Document(io.BytesIO(to_docx(doc))).paragraphs)
    assert "POV / FIX scope" in text and "review required" in text
    assert safe_filename("Copy Actuals / v2", "md") == "Copy_Actuals_v2_documentation.md"
