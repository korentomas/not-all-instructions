# experiments/tests/test_providers.py
import pytest
from harness.providers import get_provider, Message


def test_get_provider_anthropic():
    provider = get_provider("anthropic", "claude-sonnet-4-6-20250514")
    assert provider.name == "anthropic"


def test_get_provider_openai():
    provider = get_provider("openai", "codex-mini-latest")
    assert provider.name == "openai"


def test_get_provider_google():
    provider = get_provider("google", "gemini-2.0-flash")
    assert provider.name == "google"


def test_get_provider_unknown_raises():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider("unknown", "model")


def test_message_dataclass():
    msg = Message(role="user", content="hello")
    assert msg.role == "user"
    assert msg.content == "hello"
    assert msg.tool_calls is None
