import pytest
from pydantic import ValidationError

from app.config.settings import Settings


def _settings(**env: str) -> Settings:
    return Settings(_env_file=None, **env)  # type: ignore[call-arg]


def test_defaults_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("REDDIT_CLIENT_ID", "OPENAI_API_KEY", "PINECONE_API_KEY", "CHUNK_SIZE"):
        monkeypatch.delenv(key, raising=False)
    s = _settings()
    assert s.REDDIT_CLIENT_ID is None
    assert s.CHUNK_SIZE == 1000
    assert s.EMBEDDING_MODEL == "text-embedding-3-small"


def test_env_overrides_and_secret_not_in_repr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PINECONE_API_KEY", "pc-secret")
    monkeypatch.setenv("CHUNK_SIZE", "500")
    s = _settings()
    assert s.CHUNK_SIZE == 500
    assert s.PINECONE_API_KEY is not None
    assert s.PINECONE_API_KEY.get_secret_value() == "pc-secret"
    assert "pc-secret" not in repr(s)


def test_invalid_chunk_size_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHUNK_SIZE", "0")
    with pytest.raises(ValidationError):
        _settings()
