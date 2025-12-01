"""
Minimal tractionbuild package shim.

This file makes `import tractionbuild` and `import tractionbuild.check_connection`
work for test-runner and tooling that expects a package under src/.
"""

__all__ = ["check_connection"]

# Version string kept in one place; update as appropriate.
__version__ = "0.2.0"