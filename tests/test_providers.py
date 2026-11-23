import pytest

from core import llm_client


@pytest.mark.parametrize(
    "provider, host, model",
    [
        ("gemini", "generativelanguage.googleapis.com", "gemini-3.5-flash-lite"),
        ("groq", "api.groq.com", "openai/gpt-oss-120b"),
        ("mistral", "api.mistral.ai", "mistral-small-latest"),
        ("openrouter", "openrouter.ai", "openrouter/free"),
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


class _FakeAPIError(Exception):
    def __init__(self, status_code=None):
        super().__init__("provider error")
        self.status_code = status_code


class RateLimitError(Exception):
    """Same class name the OpenAI and Anthropic SDKs use."""


class APITimeoutError(Exception):
    pass


@pytest.mark.parametrize(
    "exc, error_type, phrase",
    [
        (_FakeAPIError(429), "rate_limit", "usage limit"),
        (RateLimitError(), "rate_limit", "usage limit"),
        (_FakeAPIError(401), "auth", "API key"),
        (_FakeAPIError(404), "model_not_found", "LLM_MODEL"),
        (APITimeoutError(), "timeout", "too long"),
        (_FakeAPIError(503), "provider_down", "temporary"),
    ],
)
def test_provider_errors_get_clear_messages(exc, error_type, phrase):
    err = llm_client.explain_provider_error(exc)
    assert err.error_type == error_type and phrase in str(err)


def test_generate_wraps_sdk_errors():
    class Failing:
        def complete(self, system, user):
            raise _FakeAPIError(429)

    llm_client._cache.clear()
    with pytest.raises(llm_client.LLMError) as info:
        llm_client.generate("s", "u", llm_client.BaseModel, Failing())
    assert info.value.error_type == "rate_limit"


def test_reasoning_effort_is_sent_only_when_set(monkeypatch):
    sent = {}

    class FakeCompletions:
        def create(self, **kwargs):
            sent.update(kwargs)

            class R:
                choices = [type("C", (), {"message": type("M", (), {"content": "{}"})()})()]
            return R()

    p = llm_client.OpenAIProvider("m", "k", 5, "https://api.groq.com/openai/v1")
    p.client = type("Cl", (), {"chat": type("Ch", (), {"completions": FakeCompletions()})()})()

    monkeypatch.setattr(llm_client, "REASONING_EFFORT", None)
    p.complete("s", "u")
    assert "reasoning_effort" not in sent

    monkeypatch.setattr(llm_client, "REASONING_EFFORT", "low")
    p.complete("s", "u")
    assert sent["reasoning_effort"] == "low"


def test_reasoning_effort_not_sent_to_providers_that_reject_it(monkeypatch):
    sent = {}

    class FakeCompletions:
        def create(self, **kwargs):
            sent.update(kwargs)

            class R:
                choices = [type("C", (), {"message": type("M", (), {"content": "{}"})()})()]
            return R()

    monkeypatch.setenv("LLM_PROVIDER", "mistral")
    monkeypatch.setenv("LLM_API_KEY", "test-key-not-real")
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.setattr(llm_client, "REASONING_EFFORT", "low")
    p = llm_client.get_provider()
    p.client = type("Cl", (), {"chat": type("Ch", (), {"completions": FakeCompletions()})()})()
    p.complete("s", "u")
    assert "reasoning_effort" not in sent
