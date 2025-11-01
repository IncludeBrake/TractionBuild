import os, importlib, pytest

def test_missing_required_env(monkeypatch):
    monkeypatch.setenv("ENV", "test")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        from src.tractionbuild.core import settings
        importlib.reload(settings)
        settings.get_settings()