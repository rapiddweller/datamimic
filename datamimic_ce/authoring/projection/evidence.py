# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""JSON response samples projected after validation of the complete capture."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import JsonValue

from datamimic_ce.authoring.domain.capture import CapturedProducts, validate_capture_values
from datamimic_ce.authoring.domain.requests import ProductEvidence


def _json_value(value: object) -> JsonValue:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Decimal | UUID):
        return str(value)
    if isinstance(value, date | datetime):
        return value.isoformat()
    if isinstance(value, list | tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        return {key: _json_value(item) for key, item in value.items()}
    raise ValueError("capture value cannot be represented as JSON evidence")


def sample_evidence(captured: CapturedProducts, sample_rows: int) -> tuple[ProductEvidence, ...]:
    if len({item.name for item in captured.products}) != len(captured.products):
        raise ValueError("capture product identities must be unique")
    validate_capture_values({item.name: item.rows for item in captured.products})
    result = []
    for product in captured.products:
        if not all(isinstance(row, dict) and all(isinstance(key, str) for key in row) for row in product.rows):
            raise ValueError("all captured rows must be objects with string field names")
        if product.capture is not None and product.capture.observed != len(product.rows):
            raise ValueError("capture provenance must match the complete row count")
        rows = []
        for row in product.rows[:sample_rows]:
            if not isinstance(row, dict):
                raise ValueError("captured row must be an object")
            rows.append({key: _json_value(value) for key, value in row.items()})
        result.append(
            ProductEvidence(name=product.name, count=len(product.rows), rows=tuple(rows), capture=product.capture)
        )
    return tuple(result)
