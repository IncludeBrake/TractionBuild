from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    API_KEY: str = "dummy_key"
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"
    ANOMALY_SCORE_THRESH: float = 0.6
    RAG_EMBEDDER: str = "mock"  # or "sbert"
    RAG_CHUNK_TOKENS: int = 400
    RAG_CHUNK_OVERLAP: int = 60
    RAG_MIN_SCORE: float = 0.3
    REDACTION_SALT: str = "dev-salt"   # rotate in prod via Vault
    RAG_TOP_K: int = 5
    EXTRACTOR_MAX_CONTEXT_CHARS: int = 1200
    RAG_K: int = 4
    RAG_MAX_CONTEXT_CHARS: int = 800
    RAG_CTX_MAX_TOKENS: int = 600
    RATE_QPS: int = 5            # if you later want to wire these in
    LAT_WIN_SIZE: int = 200
    DEFAULT_LLM_MODEL_SOFT: str = "gpt-4o-mini"  # same/downgrade; override in prod

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings