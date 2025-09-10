from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    vault_url: str = "http://localhost:8200"
    secret_key: str = "default-secret"
    database_url: str = "postgresql://user:password@localhost:5432/tractionbuild"
    max_tokens_per_crew: int = 1000

    class Config:
        env_prefix = "TRACTION_"
        case_sensitive = False

settings = Settings()
