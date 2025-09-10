def get_secret(name: str) -> str:
    from src.tractionbuild.core.config import settings
    return getattr(settings, name, "")
