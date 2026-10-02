"""Runtime-owned execution of user-provided script plugins."""

from __future__ import annotations


def execute_script(source: str, namespace: dict[str, object]) -> None:
    """Execute a setup script in the supplied namespace, preserving Python's globals/locals rules."""
    exec(source, namespace)


__all__ = ["execute_script"]
