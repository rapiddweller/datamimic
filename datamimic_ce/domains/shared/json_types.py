"""Types for values crossing the domain JSON boundary."""

from typing import TypeAlias

from pydantic import JsonValue

JsonObject: TypeAlias = dict[str, JsonValue]
