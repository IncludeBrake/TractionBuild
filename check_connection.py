# check_connection.py — compatibility shim for tests
try:
    # Preferred: new package path
    from tractionbuild.api.health import (
        check_connection,
        get_connection_info,
        health_check,
    )
except Exception:
    # Fallback if you haven't moved the module yet
    from tractionbuild.api.health import (
        check_connection,
        get_connection_info,
        health_check,
    )

__all__ = ["check_connection", "get_connection_info", "health_check"]
