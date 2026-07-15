# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.

"""Repair-oriented projection of canonical authoring-intent validation errors."""

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import StrEnum
from typing import Any

from pydantic import JsonValue, TypeAdapter, ValidationError

from datamimic_ce.authoring.contracts import (
    IntentValidationIssue,
    IntentValidationIssueCode,
    ReplaceFieldRepair,
)
from datamimic_ce.authoring.spec import (
    INTENT_REPAIR_ALIASES_SCHEMA_KEY,
    AuthoringSpecV1,
    IntentModelValidationIssueType,
)


class _PydanticIssueType(StrEnum):
    EXTRA_FORBIDDEN = "extra_forbidden"
    MISSING = "missing"
    UNION_TAG_INVALID = "union_tag_invalid"
    UNION_TAG_NOT_FOUND = "union_tag_not_found"


_ROOT_SCHEMA = AuthoringSpecV1.model_json_schema()
_JSON_OBJECT_ADAPTER: TypeAdapter[dict[str, JsonValue]] = TypeAdapter(
    dict[str, JsonValue]
)
_MIN_REPLACEMENT_SIMILARITY = 0.72
_MIN_REPLACEMENT_MARGIN = 0.10


@dataclass(frozen=True)
class _ValidationLocation:
    path: tuple[str | int, ...]
    owner_schema: Mapping[str, Any] | None
    raw_owner: Mapping[str, Any] | None


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


def _validation_location(
    location: tuple[str | int, ...],
    raw: Mapping[str, Any],
) -> _ValidationLocation:
    """Resolve a public path and its exact schema/raw owner without union labels."""

    schema: Mapping[str, Any] = _ROOT_SCHEMA
    current: object = raw
    public: list[str | int] = []
    owner_schema: Mapping[str, Any] | None = None
    raw_owner: Mapping[str, Any] | None = None
    index = 0
    while index < len(location):
        schema, index = _selected_union_schema(schema, current, location, index)
        if index >= len(location):
            break
        part = location[index]
        public.append(part)
        index += 1
        resolved = _resolve_schema(schema)
        if index == len(location):
            owner_schema = resolved
            raw_owner = current if isinstance(current, Mapping) else None
            break
        if isinstance(part, int):
            items = resolved.get("items")
            schema = items if isinstance(items, Mapping) else {}
            if (
                isinstance(current, Sequence)
                and not isinstance(current, str)
                and 0 <= part < len(current)
            ):
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
    return _ValidationLocation(
        path=tuple(public),
        owner_schema=owner_schema,
        raw_owner=raw_owner,
    )


def _issue_code(
    issue_type: _PydanticIssueType | None,
    intent_issue_type: IntentModelValidationIssueType | None,
) -> IntentValidationIssueCode:
    if (
        intent_issue_type
        is IntentModelValidationIssueType.UNSUPPORTED_NESTED_PRODUCT_CHILDREN
    ):
        return IntentValidationIssueCode.UNSUPPORTED_INTENT
    if issue_type is None:
        return IntentValidationIssueCode.CONSTRAINT_VIOLATION
    if issue_type is _PydanticIssueType.EXTRA_FORBIDDEN:
        return IntentValidationIssueCode.UNKNOWN_FIELD
    if issue_type is _PydanticIssueType.MISSING:
        return IntentValidationIssueCode.MISSING_FIELD
    return IntentValidationIssueCode.INVALID_DISCRIMINATOR


def _replace_field(
    raw: Mapping[str, Any],
    path: tuple[str | int, ...],
    replacement: str,
) -> tuple[dict[str, JsonValue], JsonValue] | None:
    if not path or not isinstance(path[-1], str):
        return None
    rejected = path[-1]
    document = deepcopy(dict(raw))
    current: object = document
    for part in path[:-1]:
        if isinstance(part, str):
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
            continue
        if not isinstance(current, list) or not 0 <= part < len(current):
            return None
        current = current[part]
    if (
        not isinstance(current, dict)
        or rejected not in current
        or replacement in current
    ):
        return None
    raw_rejected_value = current.pop(rejected)
    try:
        rejected_value = _JSON_OBJECT_ADAPTER.validate_python(
            {"value": raw_rejected_value}
        )["value"]
    except ValidationError:
        return None
    current[replacement] = rejected_value
    try:
        AuthoringSpecV1.model_validate(document)
    except ValidationError as error:
        owner_prefix = path[:-1]
        corrected_locations = (
            _validation_location(tuple(issue["loc"]), document).path
            for issue in error.errors()
        )
        if any(
            location[: len(owner_prefix)] == owner_prefix
            for location in corrected_locations
        ):
            return None
    try:
        corrected_fragment = _JSON_OBJECT_ADAPTER.validate_python(current)
    except ValidationError:
        return None
    return corrected_fragment, rejected_value


def _replacement_repair(
    raw: Mapping[str, Any],
    location: _ValidationLocation,
    allowed_fields: tuple[str, ...],
) -> ReplaceFieldRepair | None:
    """Return one model-backed, full-document-valid replacement or no action.

    Exact aliases come from the resolved owner's field schema. Without that
    model-owned evidence, a field must clear a high SequenceMatcher threshold
    and an ambiguity margin. Every surviving candidate is applied to a deep
    copy and validated in the complete AuthoringSpecV1 context. Errors outside
    the corrected owner may remain, but that owner must be valid and exactly
    one candidate may survive.
    """

    if (
        not location.path
        or not isinstance(location.path[-1], str)
        or location.raw_owner is None
        or location.owner_schema is None
    ):
        return None
    rejected = location.path[-1]
    properties = location.owner_schema.get("properties")
    if not isinstance(properties, Mapping):
        return None
    candidates = [
        field
        for field in allowed_fields
        if field != rejected and field not in location.raw_owner
    ]
    ranked = sorted(
        (
            (
                SequenceMatcher(
                    None,
                    rejected,
                    candidate,
                    autojunk=False,
                ).ratio(),
                candidate,
            )
            for candidate in candidates
        ),
        key=lambda item: (-item[0], item[1]),
    )
    alias_candidates: list[str] = []
    for candidate in candidates:
        property_schema = properties.get(candidate)
        if not isinstance(property_schema, Mapping):
            continue
        aliases = property_schema.get(INTENT_REPAIR_ALIASES_SCHEMA_KEY)
        if (
            isinstance(aliases, Sequence)
            and not isinstance(aliases, str)
            and rejected in aliases
        ):
            alias_candidates.append(candidate)

    selected: list[str]
    if alias_candidates:
        selected = sorted(alias_candidates)
    elif not ranked or ranked[0][0] < _MIN_REPLACEMENT_SIMILARITY or (
        len(ranked) > 1
        and ranked[1][0] >= _MIN_REPLACEMENT_SIMILARITY
        and ranked[0][0] - ranked[1][0] < _MIN_REPLACEMENT_MARGIN
    ):
        return None
    else:
        selected = [ranked[0][1]]

    validated = [
        (replacement, corrected)
        for replacement in selected
        if (corrected := _replace_field(raw, location.path, replacement)) is not None
    ]
    if len(validated) != 1:
        return None
    replacement, (corrected_fragment, rejected_value) = validated[0]
    try:
        return ReplaceFieldRepair(
            replacement_field=replacement,
            rejected_value=rejected_value,
            corrected_fragment=corrected_fragment,
        )
    except ValidationError:
        return None


def _repair_context(
    raw: Mapping[str, Any],
    location: _ValidationLocation,
) -> tuple[
    tuple[str, ...],
    str | None,
    ReplaceFieldRepair | None,
]:
    if location.owner_schema is None or location.raw_owner is None:
        return (), None, None
    properties = location.owner_schema.get("properties")
    if not isinstance(properties, Mapping):
        return (), None, None
    allowed_fields = tuple(
        name for name in properties if isinstance(name, str)
    )
    title = location.owner_schema.get("title")
    model_name = title if isinstance(title, str) else None
    repair = _replacement_repair(raw, location, allowed_fields)
    return allowed_fields, model_name, repair


def project_validation_issues(
    error: ValidationError,
    raw: Mapping[str, Any],
) -> tuple[IntentValidationIssue, ...]:
    source = error.errors()
    public = [
        (_validation_location(tuple(issue["loc"]), raw), issue)
        for issue in source
    ]
    filtered = [
        (location, issue)
        for location, issue in public
        if not any(
            other_location.path[: len(location.path)] == location.path
            and len(other_location.path) > len(location.path)
            for other_location, _ in public
        )
    ]
    result: list[IntentValidationIssue] = []
    for location, issue in filtered:
        path = location.path
        raw_issue_type = issue["type"]
        if not isinstance(raw_issue_type, str):
            issue_type = None
            intent_issue_type = None
        else:
            try:
                intent_issue_type = IntentModelValidationIssueType(raw_issue_type)
            except ValueError:
                intent_issue_type = None
            try:
                issue_type = _PydanticIssueType(raw_issue_type)
            except ValueError:
                issue_type = None
        code = _issue_code(issue_type, intent_issue_type)
        allowed_fields: tuple[str, ...] = ()
        model_name: str | None = None
        repair: ReplaceFieldRepair | None = None
        if code is IntentValidationIssueCode.UNKNOWN_FIELD:
            allowed_fields, model_name, repair = _repair_context(
                raw,
                location,
            )
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
                repair=repair,
            )
        )
    return tuple(result)


__all__ = [
    "project_validation_issues",
]
