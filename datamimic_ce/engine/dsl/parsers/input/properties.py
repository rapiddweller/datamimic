"""Parsing for Java-style properties files used by DSL descriptors."""

from pathlib import Path

_PROPERTY_LINES: dict[str, tuple[str, ...]] = {}


def _read_property_lines(path: Path, encoding: str) -> tuple[str, ...]:
    cache_key = str(path)
    if cache_key not in _PROPERTY_LINES:
        try:
            with path.open("r", encoding=encoding) as properties_file:
                _PROPERTY_LINES[cache_key] = tuple(properties_file)
        except FileNotFoundError as error:
            raise FileNotFoundError(
                f"Property file not found {str(path)}, please check the file path again. Error message: {error}"
            ) from error
    return _PROPERTY_LINES[cache_key]


def parse_properties(path: Path, encoding: str = "utf-8") -> dict[str, str]:
    properties: dict[str, str] = {}
    for raw_line in _read_property_lines(path, encoding):
        line = raw_line.strip()
        if line and not line.startswith("#"):
            key, value = line.split("=", 1)
            properties[key.strip()] = value.strip()
    return properties
