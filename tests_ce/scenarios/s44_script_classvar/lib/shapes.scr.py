from dataclasses import dataclass, fields
from typing import ClassVar


@dataclass
class Shape:
    sides: int
    kind: ClassVar[str] = "polygon"


def field_count():
    return len(fields(Shape))


def kind():
    return Shape.kind
