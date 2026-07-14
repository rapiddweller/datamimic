# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.

"""Repair-oriented projection of canonical authoring-intent validation errors."""

from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Any

from pydantic import ValidationError

from datamimic_ce.authoring.contracts import IntentValidationIssue, IntentValidationIssueCode
from datamimic_ce.authoring.spec import AuthoringSpecV1, ProductIntentKind
from datamimic_ce.authoring.spec_examples import minimal_product_example


class _PydanticIssueType(StrEnum):
    EXTRA_FORBIDDEN = "extra_forbidden"
    MISSING = "missing"
    UNION_TAG_INVALID = "union_tag_invalid"
    UNION_TAG_NOT_FOUND = "union_tag_not_found"


_ROOT_SCHEMA = AuthoringSpecV1.model_json_schema()


def _resolve_schema(schema: Mapping[str, Any]) -> Mapping[str, Any]:
    reference = schema.get("$ref")
    if not isinstance(reference, str):
        return schema
    prefix = "#/$defs/"
    if not reference.startswith(prefix):
        return schema
    definitions = _ROOT_SCHEMA.get("$defs")
    if not isinstance(definitions, Mapping):
        return schema
    resolved = definitions.get(reference.removeprefix(prefix))
    return resolved if isinstance(resolved, Mapping) else schema


def _selected_union_schema(
    schema: Mapping[str, Any],
    raw: object,
    location: tuple[str | int, ...],
    index: int,
) -> tuple[Mapping[str, Any], int]:
    resolved = _resolve_schema(schema)
    discriminator = resolved.get("discriminator")
    if not isinstance(discriminator, Mapping) or not isinstance(raw, Mapping):
        return resolved, index
    property_name = discriminator.get("propertyName")
    mapping = discriminator.get("mapping")
    if not isinstance(property_name, str) or not isinstance(mapping, Mapping):
        return resolved, index
    selected = raw.get(property_name)
    if not isinstance(selected, str):
        return resolved, index
    reference = mapping.get(selected)
    if not isinstance(reference, str):
        return resolved, index
    branch_schema = _resolve_schema({"$ref": reference})
    if index < len(location) and location[index] == selected:
        return branch_schema, index + 1
    return branch_schema, index


def normalize_validation_path(
    location: tuple[str | int, ...],
    raw: Mapping[str, Any],
) -> tuple[str | int, ...]:
    """Remove union labels only at schema-proven discriminated-union positions."""

    schema: Mapping[str, Any] = _ROOT_SCHEMA
    current: object = raw
    public: list[str | int] = []
    index = 0
    while index < len(location):
        schema, index = _selected_union_schema(schema, current, location, index)
        if index >= len(location):
            break
        part = location[index]
        public.append(part)
        index += 1
        resolved = _resolve_schema(schema)
        if isinstance(part, int):
            items = resolved.get("items")
            schema = items if isinstance(items, Mapping) else {}
            if isinstance(current, Sequence) and not isinstance(current, str) and part < len(current):
                current = current[part]
            continue
        properties = resolved.get("properties")
        if isinstance(properties, Mapping):
            property_schema = properties.get(part)
            schema = property_schema if isinstance(property_schema, Mapping) else {}
        else:
            schema = {}
        if isinstance(current, Mapping) and part in current:
            current = current[part]
    return tuple(public)


def _issue_code(issue_type: str) -> IntentValidationIssueCode:
    try:
        typed = _PydanticIssueType(issue_type)
    except ValueError:
        return IntentValidationIssueCode.CONSTRAINT_VIOLATION
    if typed is _PydanticIssueType.EXTRA_FORBIDDEN:
        return IntentValidationIssueCode.UNKNOWN_FIELD
    if typed is _PydanticIssueType.MISSING:
        return IntentValidationIssueCode.MISSING_FIELD
    return IntentValidationIssueCode.INVALID_DISCRIMINATOR


def _product_repair_context(
    raw: Mapping[str, Any],
    path: tuple[str | int, ...],
) -> tuple[tuple[str, ...], dict[str, Any] | None, str | None]:
    if len(path) < 3 or path[0] != "products" or not isinstance(path[1], int):
        return (), None, None
    products = raw.get("products")
    if not isinstance(products, list) or path[1] >= len(products):
        return (), None, None
    product = products[path[1]]
    if not isinstance(product, Mapping):
        return (), None, None
    raw_kind = product.get("kind")
    if not isinstance(raw_kind, str):
        return (), None, None
    try:
        kind = ProductIntentKind(raw_kind)
    except ValueError:
        return (), None, None
    model = minimal_product_example(kind)
    model_type = type(model)
    return (
        tuple(model_type.model_fields),
        model.model_dump(mode="json", exclude_none=True),
        model_type.__name__,
    )


def project_validation_issues(
    error: ValidationError,
    raw: Mapping[str, Any],
) -> tuple[IntentValidationIssue, ...]:
    source = error.errors(include_url=False)
    public = [
        (normalize_validation_path(tuple(issue["loc"]), raw), issue)
        for issue in source
    ]
    filtered = [
        (path, issue)
        for path, issue in public
        if not any(
            other_path[: len(path)] == path and len(other_path) > len(path)
            for other_path, _ in public
        )
    ]
    result: list[IntentValidationIssue] = []
    for path, issue in filtered:
        code = _issue_code(str(issue["type"]))
        allowed_fields: tuple[str, ...] = ()
        expected_fragment: dict[str, Any] | None = None
        model_name: str | None = None
        if code is IntentValidationIssueCode.UNKNOWN_FIELD:
            allowed_fields, expected_fragment, model_name = _product_repair_context(raw, path)
        message = str(issue["msg"])
        if code is IntentValidationIssueCode.UNKNOWN_FIELD and path:
            owner = f" for {model_name}" if model_name is not None else ""
            message = f"Unknown field '{path[-1]}'{owner}"
        result.append(
            IntentValidationIssue(
                path=path,
                code=code,
                message=message,
                allowed_fields=allowed_fields,
                expected_fragment=expected_fragment,
            )
        )
    return tuple(result)


def unsupported_intent_issues(errors: list[str]) -> tuple[IntentValidationIssue, ...]:
    return tuple(
        IntentValidationIssue(
            path=("spec",),
            code=IntentValidationIssueCode.UNSUPPORTED_INTENT,
            message=message,
        )
        for message in errors
    )


__all__ = [
    "normalize_validation_path",
    "project_validation_issues",
    "unsupported_intent_issues",
]
