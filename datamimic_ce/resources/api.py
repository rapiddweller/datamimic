"""Public access to packaged demo resources."""

from collections.abc import Iterator
from importlib.abc import Traversable
from importlib.resources import files


def demo_root() -> Traversable:
    """Return the packaged demos directory without coercing it to a filesystem path."""
    return files("datamimic_ce.resources").joinpath("demos")


def demo_names() -> Iterator[str]:
    """Iterate names of packaged demo directories."""
    return (item.name for item in demo_root().iterdir() if item.is_dir())


__all__ = ["demo_names", "demo_root"]
