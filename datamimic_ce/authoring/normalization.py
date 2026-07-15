# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Lossless compatibility normalization into :class:`AuthoringSpecV1`.

This boundary accepts the historical compact scaffold shape and performs only
structural or lexical aliasing.  Unsupported or ambiguous intent is reported;
it is never repaired by changing field semantics.
"""

from __future__ import annotations

import ast
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from datamimic_ce.authoring.contracts import IntentValidationIssue
from datamimic_ce.authoring.intent_validation import (
    project_validation_issues,
    unsupported_intent_issues,
)
from datamimic_ce.authoring.spec import AuthoringSpecV1, FieldIntentKind
from datamimic_ce.constants.element_constants import EL_GENERATE
from datamimic_ce.exporters.exporter_util import buffered_exporter_names
from datamimic_ce.model.constraints import is_source_file


class NormalizationResult(BaseModel):
    """Typed result; failures never carry a partially valid authoring spec."""

    model_config = ConfigDict(frozen=True)

    spec: AuthoringSpecV1 | None = None
    notes: tuple[str, ...] = ()
    issues: tuple[IntentValidationIssue, ...] = ()

    @property
    def errors(self) -> tuple[str, ...]:
        """Compatibility summaries projected from canonical typed issues."""

        return tuple(issue.summary() for issue in self.issues)


_KIND_ALIASES: dict[str, FieldIntentKind] = {
    "id": FieldIntentKind.INCREMENT,
    "auto": FieldIntentKind.INCREMENT,
    "sequence": FieldIntentKind.INCREMENT,
    "autoincrement": FieldIntentKind.INCREMENT,
    "name": FieldIntentKind.PERSON_NAME,
    "fullname": FieldIntentKind.PERSON_NAME,
    "full_name": FieldIntentKind.PERSON_NAME,
    "person": FieldIntentKind.PERSON_NAME,
    "email": FieldIntentKind.PERSON_EMAIL,
    "int": FieldIntentKind.INTEGER_RANGE,
    "integer": FieldIntentKind.INTEGER_RANGE,
    "number": FieldIntentKind.INTEGER_RANGE,
    "number_range": FieldIntentKind.INTEGER_RANGE,
    "float": FieldIntentKind.DECIMAL_RANGE,
    "decimal": FieldIntentKind.DECIMAL_RANGE,
    "money": FieldIntentKind.DECIMAL_RANGE,
    "string": FieldIntentKind.STRING_LENGTH,
    "str": FieldIntentKind.STRING_LENGTH,
    "text": FieldIntentKind.STRING_LENGTH,
    "enum": FieldIntentKind.VALUES,
    "choice": FieldIntentKind.VALUES,
    "choices": FieldIntentKind.VALUES,
    "categorical": FieldIntentKind.VALUES,
    "category": FieldIntentKind.VALUES,
    "weighted_values": FieldIntentKind.WEIGHTED,
    "weighted values": FieldIntentKind.WEIGHTED,
    "weighted_choice": FieldIntentKind.WEIGHTED,
    "regex": FieldIntentKind.PATTERN,
    "const": FieldIntentKind.CONSTANT,
    "fixed": FieldIntentKind.CONSTANT,
    "expression": FieldIntentKind.SCRIPT,
    "formula": FieldIntentKind.SCRIPT,
    "computed": FieldIntentKind.SCRIPT,
    "nested": FieldIntentKind.NESTED_LIST,
    "list": FieldIntentKind.NESTED_LIST,
    "array": FieldIntentKind.NESTED_LIST,
    "object": FieldIntentKind.NESTED_LIST,
}

_LEGACY_KEYS_BY_FIELD_KIND: dict[FieldIntentKind, frozenset[str]] = {
    FieldIntentKind.INCREMENT: frozenset(),
    FieldIntentKind.PERSON_NAME: frozenset(),
    FieldIntentKind.PERSON_EMAIL: frozenset(),
    FieldIntentKind.INTEGER_RANGE: frozenset(("min", "max", "unique")),
    FieldIntentKind.DECIMAL_RANGE: frozenset(("min", "max")),
    FieldIntentKind.STRING_LENGTH: frozenset(("min", "max")),
    FieldIntentKind.VALUES: frozenset(("values",)),
    FieldIntentKind.WEIGHTED: frozenset(("values", "weights")),
    FieldIntentKind.PATTERN: frozenset(("pattern",)),
    FieldIntentKind.CONSTANT: frozenset(("value",)),
    FieldIntentKind.SCRIPT: frozenset(("script",)),
    FieldIntentKind.NESTED_LIST: frozenset(("min", "max", "fields", "children")),
}


def _one_alias(mapping: dict[str, Any], aliases: tuple[str, ...], label: str, errors: list[str]) -> Any:
    present = [name for name in aliases if name in mapping]
    if len(present) > 1:
        values = [mapping[name] for name in present]
        if any(value != values[0] for value in values[1:]):
            errors.append(f"conflicting aliases for {label}: {', '.join(present)}")
            return None
    return mapping[present[0]] if present else None


def _objects(
    value: Any,
    *,
    label: str,
    notes: list[str],
    errors: list[str],
) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, dict):
        notes.append(f"object-shaped '{label}' normalized to a one-item list")
        values = [value]
    elif isinstance(value, list):
        values = value
    else:
        errors.append(f"{label} must be an array of objects, got {type(value).__name__}")
        return []
    result: list[dict[str, Any]] = []
    for index, item in enumerate(values):
        if not isinstance(item, dict):
            errors.append(f"{label} item {index} must be an object, got {type(item).__name__}")
        else:
            result.append(item)
    return result


def _normalize_kind(
    raw: Any,
    field_name: str,
    notes: list[str],
    errors: list[str],
) -> FieldIntentKind | None:
    if not isinstance(raw, str):
        errors.append(f"unsupported field kind '{raw!r}' on field '{field_name}'")
        return None
    value = raw.strip().lower()
    alias_kind = _KIND_ALIASES.get(value)
    candidate = alias_kind if alias_kind is not None else value
    try:
        kind = FieldIntentKind(candidate)
    except ValueError:
        errors.append(f"unsupported field kind '{value or '<missing>'}' on field '{field_name}'")
        return None
    if alias_kind is not None:
        notes.append(f"field '{field_name}': kind '{value}' normalized to '{kind.value}'")
    return kind


def _calls_unsupported_unique_helper(script: object) -> bool:
    """Recognize invented helper calls without rejecting ordinary identifiers."""

    try:
        tree = ast.parse(str(script), mode="eval")
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        leaf = function.id if isinstance(function, ast.Name) else None
        if isinstance(function, ast.Attribute):
            leaf = function.attr
        if leaf is None:
            continue
        if leaf == "unique" or leaf.startswith("unique_") or leaf.endswith("_unique"):
            return True
    return False


def _normalize_field(
    field: dict[str, Any],
    *,
    product_name: str,
    nested: bool,
    notes: list[str],
    errors: list[str],
) -> dict[str, Any] | None:
    name = _legacy_field_name(field, product_name, notes, errors)
    kind = _legacy_field_kind(field, name, notes, errors)
    if kind is None:
        return None
    _validate_legacy_field_shape(field, name, kind, errors)
    result: dict[str, Any] = {"kind": kind, "name": name}
    _normalize_field_payload(
        result,
        field,
        name=name,
        kind=kind,
        product_name=product_name,
        nested=nested,
        notes=notes,
        errors=errors,
    )
    return result


def _legacy_field_name(
    field: dict[str, Any],
    product_name: str,
    notes: list[str],
    errors: list[str],
) -> str:
    name = _one_alias(field, ("name", "field", "column"), "field name", errors)
    if not isinstance(name, str) or not name.strip():
        errors.append(f"field in product '{product_name}' requires a non-empty name")
        return "<invalid>"
    if "name" not in field:
        used = "field" if "field" in field else "column"
        notes.append(f"field '{name}': key '{used}' normalized to 'name'")
    return name


def _legacy_field_kind(
    field: dict[str, Any],
    name: str,
    notes: list[str],
    errors: list[str],
) -> FieldIntentKind | None:
    raw_kind = _one_alias(field, ("kind", "type"), f"kind of field '{name}'", errors)
    if "kind" not in field and "type" in field:
        notes.append(f"field '{name}': key 'type' normalized to 'kind'")
    return _normalize_kind(raw_kind, name, notes, errors)


def _validate_legacy_field_shape(
    field: dict[str, Any],
    name: str,
    kind: FieldIntentKind,
    errors: list[str],
) -> None:

    if "script" in field and _calls_unsupported_unique_helper(field["script"]):
        errors.append(
            f"field '{name}': invented unique helper/script is unsupported; use "
            "kind='int_range' with explicit unique=true"
        )

    common = {"name", "field", "column", "kind", "type"}
    unknown = sorted(set(field) - common - _LEGACY_KEYS_BY_FIELD_KIND[kind])
    if unknown:
        errors.append(f"unknown or incompatible key(s) on field '{name}': {', '.join(unknown)}")

    if kind is FieldIntentKind.CONSTANT and "values" in field:
        errors.append(f"field '{name}': constant with values is ambiguous; choose kind='values' explicitly")
    if kind in (FieldIntentKind.VALUES, FieldIntentKind.WEIGHTED) and "values" not in field:
        errors.append(f"field '{name}' of kind '{kind}' requires an explicit values array")


def _normalize_field_payload(
    result: dict[str, Any],
    field: dict[str, Any],
    *,
    name: str,
    kind: FieldIntentKind,
    product_name: str,
    nested: bool,
    notes: list[str],
    errors: list[str],
) -> None:
    if kind in (
        FieldIntentKind.INTEGER_RANGE,
        FieldIntentKind.DECIMAL_RANGE,
        FieldIntentKind.STRING_LENGTH,
    ):
        if "min" not in field or "max" not in field:
            errors.append(f"field '{name}' of kind '{kind}' requires explicit min and max")
        result["minimum"] = field.get("min")
        result["maximum"] = field.get("max")
    if kind is FieldIntentKind.INTEGER_RANGE:
        result["unique"] = field.get("unique", False)
        if nested and result["unique"]:
            errors.append(f"unsupported feature: unique=true inside nested list field '{name}'")
    elif kind is FieldIntentKind.VALUES:
        result["values"] = field.get("values")
    elif kind is FieldIntentKind.WEIGHTED:
        result["values"] = field.get("values")
        result["weights"] = field.get("weights")
    elif kind is FieldIntentKind.PATTERN:
        result["pattern"] = field.get("pattern")
    elif kind is FieldIntentKind.CONSTANT:
        result["value"] = field.get("value")
    elif kind is FieldIntentKind.SCRIPT:
        result["script"] = field.get("script")
    elif kind is FieldIntentKind.NESTED_LIST:
        _normalize_nested_field(
            result,
            field,
            name=name,
            product_name=product_name,
            nested=nested,
            notes=notes,
            errors=errors,
        )


def _normalize_nested_field(
    result: dict[str, Any],
    field: dict[str, Any],
    *,
    name: str,
    product_name: str,
    nested: bool,
    notes: list[str],
    errors: list[str],
) -> None:
    if nested:
        errors.append(
            f"unsupported feature: nested field '{name}' more than one level deep in product '{product_name}'"
        )
    children_raw = _one_alias(
        field,
        ("fields", "children"),
        f"nested fields of '{name}'",
        errors,
    )
    if "fields" not in field and "children" in field:
        notes.append(f"nested field '{name}': key 'children' normalized to 'fields'")
    children = _objects(
        children_raw,
        label=f"nested fields of field '{name}'",
        notes=notes,
        errors=errors,
    )
    result["minimum_count"] = field.get("min")
    result["maximum_count"] = field.get("max")
    result["fields"] = [
        normalized
        for child in children
        if (
            normalized := _normalize_field(
                child,
                product_name=product_name,
                nested=True,
                notes=notes,
                errors=errors,
            )
        )
        is not None
    ]


def _normalize_targets(raw: Any, product_name: str, errors: list[str]) -> list[dict[str, Any]]:
    if raw is None or raw == "":
        return []
    if not isinstance(raw, str):
        errors.append(f"target of product '{product_name}' must be a comma-separated string")
        return []
    targets: list[dict[str, Any]] = []
    seen: set[str] = set()
    formats = {name.lower(): name for name in buffered_exporter_names()}
    for token in (part.strip() for part in raw.split(",")):
        if not token:
            continue
        if token in seen:
            errors.append(f"duplicate target '{token}' on product '{product_name}'")
            continue
        seen.add(token)
        file_format = formats.get(token.lower())
        if file_format is not None:
            targets.append({"kind": "file_export", "format": file_format})
        elif token.lower().endswith(tuple(f".{fmt.lower()}" for fmt in formats)):
            errors.append(
                f"target '{token}' on product '{product_name}' looks like a filename; "
                "authoring V1 requires an explicit file_export target and export_uri"
            )
        elif token.endswith((".insert", ".update", ".upsert", ".delete")):
            errors.append(f"database or MongoDB target '{token}' is unsupported by authoring V1")
        else:
            targets.append({"kind": "memstore", "id": token})
    return targets


def _normalize_source(
    raw: Any,
    source_type: Any,
    product_name: str,
    errors: list[str],
) -> dict[str, Any] | None:
    if not isinstance(raw, str) or not raw.strip():
        errors.append(f"source of product '{product_name}' must be a non-empty string")
        return None
    source = raw.strip()
    if is_source_file(source, EL_GENERATE):
        if source_type is not None:
            errors.append(f"file source '{source}' on product '{product_name}' cannot use source_type")
        return {"kind": "file", "path": source, "distribution": "ordered"}
    # Historical free-form non-file source tokens are memstore ids. Canonical
    # V1 intent remains explicit and discriminated; this is compatibility only.
    return {
        "kind": "memstore",
        "id": source,
        "product": source_type,
        "distribution": "ordered",
    }


def _normalize_product(
    product: dict[str, Any],
    *,
    depth: int,
    notes: list[str],
    errors: list[str],
) -> dict[str, Any] | None:
    name = _legacy_product_name(product, errors)
    _validate_legacy_product_keys(product, name, errors)
    normalized_fields = _normalize_product_fields(product, name, notes, errors)
    targets = _normalize_targets(product.get("target"), name, errors)
    children = _normalize_product_children(product, name, depth, notes, errors)
    has_source, timeseries_attrs = _validate_product_mode(product, name, children, errors)
    common: dict[str, Any] = {
        "name": name,
        "fields": normalized_fields,
        "targets": targets,
    }
    if has_source:
        return _normalized_source_product(product, name, common, errors)
    if timeseries_attrs:
        return _normalized_time_series_product(product, common)
    normalized_children = _normalize_generated_children(children, depth, notes, errors)
    return {
        "kind": "generated",
        **common,
        "count": product.get("count"),
        "children": normalized_children,
    }


def _legacy_product_name(product: dict[str, Any], errors: list[str]) -> str:
    name = product.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("every legacy generate requires a non-empty name")
        return "<invalid>"
    return name


def _validate_legacy_product_keys(
    product: dict[str, Any],
    name: str,
    errors: list[str],
) -> None:
    allowed = {
        "name",
        "count",
        "target",
        "fields",
        "keys",
        "columns",
        "source",
        "source_type",
        "type",
        "start",
        "end",
        "interval",
        "children",
        "nested",
    }
    unknown = sorted(set(product) - allowed)
    if unknown:
        errors.append(f"unknown key(s) on generate '{name}': {', '.join(unknown)}")


def _normalize_product_fields(
    product: dict[str, Any],
    name: str,
    notes: list[str],
    errors: list[str],
) -> list[dict[str, Any]]:
    fields_raw = _one_alias(product, ("fields", "keys", "columns"), f"fields of '{name}'", errors)
    used_field_alias = next((key for key in ("keys", "columns") if key in product), None)
    if "fields" not in product and used_field_alias:
        notes.append(f"generate '{name}': key '{used_field_alias}' normalized to 'fields'")
    fields = _objects(fields_raw, label=f"fields of generate '{name}'", notes=notes, errors=errors)
    return [
        normalized
        for field in fields
        if (
            normalized := _normalize_field(
                field,
                product_name=str(name),
                nested=False,
                notes=notes,
                errors=errors,
            )
        )
        is not None
    ]


def _normalize_product_children(
    product: dict[str, Any],
    name: str,
    depth: int,
    notes: list[str],
    errors: list[str],
) -> list[dict[str, Any]]:
    children_raw = _one_alias(product, ("children", "nested"), f"children of '{name}'", errors)
    if "children" not in product and "nested" in product:
        notes.append(f"generate '{name}': key 'nested' normalized to 'children'")
    children = _objects(
        children_raw,
        label=f"children of generate '{name}'",
        notes=notes,
        errors=errors,
    )
    if children and depth >= 1:
        for child in children:
            errors.append(
                f"unsupported feature: generate '{child.get('name', '<unnamed>')}' nested more "
                f"than one level deep inside '{name}'"
            )
    return children


def _validate_product_mode(
    product: dict[str, Any],
    name: str,
    children: list[dict[str, Any]],
    errors: list[str],
) -> tuple[bool, list[str]]:
    has_source = product.get("source") is not None
    timeseries_attrs = [attr for attr in ("start", "end", "interval") if product.get(attr) is not None]
    if timeseries_attrs and len(timeseries_attrs) != 3:
        errors.append(f"time-series product '{name}' requires start, end, and interval together")
    if has_source and timeseries_attrs:
        errors.append(f"product '{name}' cannot combine source and time-series intent")
    if has_source and product.get("count") is not None:
        errors.append(f"source-backed product '{name}' cannot define count; source cardinality owns row count")
    if not has_source and ("source_type" in product or "type" in product):
        errors.append(f"product '{name}' defines source_type/type without a source")
    if (has_source or timeseries_attrs) and children:
        errors.append(f"source/time-series product '{name}' cannot contain nested child products in V1")
    return has_source, timeseries_attrs


def _normalized_source_product(
    product: dict[str, Any],
    name: str,
    common: dict[str, Any],
    errors: list[str],
) -> dict[str, Any]:
    source_type = _one_alias(
        product,
        ("source_type", "type"),
        f"source type of '{name}'",
        errors,
    )
    source = _normalize_source(product.get("source"), source_type, name, errors)
    return {"kind": "source", **common, "source": source}


def _normalized_time_series_product(
    product: dict[str, Any],
    common: dict[str, Any],
) -> dict[str, Any]:
    return {
        "kind": "time_series",
        **common,
        "series_count": product.get("count", 1),
        "window": {
            "start": product.get("start"),
            "end": product.get("end"),
            "interval": product.get("interval"),
        },
    }


def _normalize_generated_children(
    children: list[dict[str, Any]],
    depth: int,
    notes: list[str],
    errors: list[str],
) -> list[dict[str, Any]]:
    normalized_children = [
        normalized
        for child in children
        if depth < 1
        and (
            normalized := _normalize_product(
                child,
                depth=depth + 1,
                notes=notes,
                errors=errors,
            )
        )
        is not None
    ]
    child_names = [str(child.get("name")) for child in normalized_children]
    duplicate_children = sorted({child_name for child_name in child_names if child_names.count(child_name) > 1})
    if duplicate_children:
        errors.append(f"product names must be unique: {', '.join(duplicate_children)}")
    for child in normalized_children:
        child["relationship"] = {"kind": "nested"}
        child.pop("children", None)
    return normalized_children


def _normalize_legacy(raw: dict[str, Any]) -> NormalizationResult:
    notes: list[str] = ["legacy scaffold document normalized to AuthoringSpecV1"]
    errors: list[str] = []
    allowed_root = {"seed", "rngSeed", "generates", "generate", "entities"}
    unknown_root = sorted(set(raw) - allowed_root)
    if unknown_root:
        errors.append(f"unknown scaffold root key(s): {', '.join(unknown_root)}")

    seed = _one_alias(raw, ("seed", "rngSeed"), "seed", errors)
    if "seed" not in raw and "rngSeed" in raw:
        notes.append("root key 'rngSeed' normalized to 'seed'")
    products_raw = _one_alias(
        raw,
        ("generates", "generate", "entities"),
        "legacy generates collection",
        errors,
    )
    used_collection_alias = next((key for key in ("generate", "entities") if key in raw), None)
    if "generates" not in raw and used_collection_alias:
        notes.append(f"root key '{used_collection_alias}' normalized to 'generates'")
    products = _objects(products_raw, label="generates", notes=notes, errors=errors)
    normalized_products = [
        normalized
        for product in products
        if (
            normalized := _normalize_product(
                product,
                depth=0,
                notes=notes,
                errors=errors,
            )
        )
        is not None
    ]
    product_names = [str(product.get("name")) for product in normalized_products]
    duplicate_products = sorted(
        {product_name for product_name in product_names if product_names.count(product_name) > 1}
    )
    if duplicate_products:
        errors.append(f"product names must be unique: {', '.join(duplicate_products)}")
    if errors:
        return NormalizationResult(notes=tuple(notes), issues=unsupported_intent_issues(errors))
    candidate = {
        "version": "1",
        "seed": seed,
        "products": normalized_products,
        "expectations": [],
    }
    try:
        spec = AuthoringSpecV1.model_validate(candidate)
    except ValidationError as error:
        return NormalizationResult(
            notes=tuple(notes),
            issues=project_validation_issues(error, candidate),
        )
    return NormalizationResult(spec=spec, notes=tuple(notes))


def normalize_authoring_spec(raw: dict[str, Any]) -> NormalizationResult:
    """Validate V1 directly or losslessly normalize one legacy scaffold document."""

    if "version" not in raw:
        return _normalize_legacy(raw)
    try:
        return NormalizationResult(spec=AuthoringSpecV1.model_validate(raw))
    except ValidationError as error:
        return NormalizationResult(issues=project_validation_issues(error, raw))


__all__ = ["NormalizationResult", "normalize_authoring_spec"]
