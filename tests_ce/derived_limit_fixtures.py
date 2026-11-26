# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.


def _flat(*counts: int) -> str:
    products = "".join(
        f'<generate name="p{index}" count="{count}"><key name="id" generator="IncrementGenerator"/></generate>'
        for index, count in enumerate(counts)
    )
    return f'<setup rngSeed="1">{products}</setup>'


def _limits(result: object) -> dict[str, int]:
    return {item.name: item.capture.limit for item in result.evidence}  # type: ignore[attr-defined]


_READBACK_ROLES = (
    {"product": "parents", "field": "id", "role": {"kind": "identifier"}},
    {
        "product": "readback",
        "field": "id",
        "role": {"kind": "foreign_key", "parent_product": "parents", "parent_field": "id"},
    },
)


def _memstore(produced: int, readback_count: str = "") -> str:
    producer = (
        f'<generate name="parents" count="{produced}" target="mem"><key name="id" generator="IncrementGenerator"/>'
        "</generate>"
    )
    readback = (
        f'<generate name="readback" source="mem" type="parents" distribution="ordered"{readback_count}>'
        '<key name="id" script="this.id"/></generate>'
    )
    return f'<setup rngSeed="7"><memstore id="mem"/>{producer}{readback}</setup>'
