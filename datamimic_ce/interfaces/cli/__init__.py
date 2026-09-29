"""CLI package; command declarations load only when the app is requested."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._app import app

__all__ = ["app"]


def __getattr__(name: str) -> object:
    if name == "app":
        from ._app import app

        return app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
