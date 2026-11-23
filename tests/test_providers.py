import pytest

from core import llm_client


@pytest.mark.parametrize(
    "provider, host, model",
    [
        ("gemini", "generativelanguage.googleapis.com", "gemini-3.5-flash"),
        ("groq", "api.groq.com", "openai/gpt-oss-120b"),
    ],
)
def test_free_providers_use_openai_compatible_endpoint(monkeypatch, provider, host, model):
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv("LLM_API_KEY", "test-key-not-real")
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    p = llm_client.get_provider()
    assert isinstance(p, llm_client.OpenAIProvider)
    assert host in str(p.client.base_url)
    assert p.model == model


def test_model_can_be_overridden(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("LLM_API_KEY", "test-key-not-real")
    monkeypatch.setenv("LLM_MODEL", "some-other-model")
    assert llm_client.get_provider().model == "some-other-model"


def test_no_key_falls_back_to_demo_mode(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    assert isinstance(llm_client.get_provider(), llm_client.MockProvider)
