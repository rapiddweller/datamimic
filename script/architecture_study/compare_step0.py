"""Fail when two Step-0 snapshots differ; no descriptor is ignored as flaky."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

LEGACY_DEMO_PREFIX = "datamimic_ce/demos/"
TARGET_DEMO_PREFIX = "datamimic_ce/resources/demos/"
_ALLOWED_ATTRIBUTES = re.compile(r"(Must defined one of following attributes \{)([^{}]*)(\})")
_TEST_EVIDENCE_LINE = re.compile(r"(tests_ce/[^:\s]+\.py):\d+")
_CAPABILITY_WORDING_CHANGES = {
    ("rules", "35", "provenance"): (
        "ExporterUtil target parser and ExportOperation enum.",
        "DSL target parser and ExportOperation enum.",
    ),
    ("rules", "36", "provenance"): (
        "TaskUtil source dispatch contract.",
        "Source routing contract.",
    ),
    ("elements", "generate", "attributes", "sourceEntity", "description"): (
        "Explicit physical entity to read/write (table/collection). "
        "Precedence: sourceEntity/targetEntity -> type -> name; "
        "absent -> existing behaviour. See StatementUtil.resolve_source/target_entity.",
        "Explicit physical entity to read/write (table/collection). "
        "Precedence: sourceEntity/targetEntity -> type -> name; "
        "absent -> existing behaviour.",
    ),
    ("elements", "generate", "attributes", "targetEntity", "description"): (
        "Explicit physical entity to read/write (table/collection). "
        "Precedence: sourceEntity/targetEntity -> type -> name; "
        "absent -> existing behaviour. See StatementUtil.resolve_source/target_entity.",
        "Explicit physical entity to read/write (table/collection). "
        "Precedence: sourceEntity/targetEntity -> type -> name; "
        "absent -> existing behaviour.",
    ),
    ("elements", "variable", "attributes", "type", "description"): (
        "Normally a scalar cast for a generated value (e.g. 'int', 'string'). "
        "When 'source' is also set, this instead selects "
        "which source-backed statement's rows to read (a producer name, not a type) — see "
        "StatementUtil.resolve_source_entity's sourceEntity -> type -> name fallback.",
        "Normally a scalar cast for a generated value (e.g. 'int', 'string'). "
        "When 'source' is also set, this instead selects "
        "which source-backed statement's rows to read (a producer name, not a type); "
        "sourceEntity -> type -> name is the fallback.",
    ),
    ("elements", "iterate", "attributes", "sourceEntity", "description"): (
        "Explicit physical entity to read/write (table/collection). "
        "Precedence: sourceEntity/targetEntity -> type -> name; "
        "absent -> existing behaviour. See StatementUtil.resolve_source/target_entity.",
        "Explicit physical entity to read/write (table/collection). "
        "Precedence: sourceEntity/targetEntity -> type -> name; "
        "absent -> existing behaviour.",
    ),
    ("elements", "iterate", "attributes", "targetEntity", "description"): (
        "Explicit physical entity to read/write (table/collection). "
        "Precedence: sourceEntity/targetEntity -> type -> name; "
        "absent -> existing behaviour. See StatementUtil.resolve_source/target_entity.",
        "Explicit physical entity to read/write (table/collection). "
        "Precedence: sourceEntity/targetEntity -> type -> name; "
        "absent -> existing behaviour.",
    ),
}
_CAPABILITY_OLD_VERSION = "4.3.1.dev89+dirty"
_CAPABILITY_TRANSITION_CHANGE = (
    ("elements", "transition", "attributes"),
    {},
    {
        "from": {"required": True, "type": "str"},
        "to": {"required": True, "type": "str"},
        "weight": {"required": False, "type": "float"},
    },
)


def normalize_error_message(message: str) -> str:
    def sort_allowed_attributes(match: re.Match[str]) -> str:
        members = match.group(2).split(", ")
        if not members or any(not (member.startswith("'") and member.endswith("'")) for member in members):
            return match.group(0)
        return match.group(1) + ", ".join(sorted(members)) + match.group(3)

    return _ALLOWED_ATTRIBUTES.sub(sort_allowed_attributes, message)


def load(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def projection_content(item: Any) -> str | None:
    if not isinstance(item, dict):
        return None
    content = item.get("content")
    if not isinstance(content, str):
        return None
    encoded = content.encode("utf-8")
    if item.get("bytes") != len(encoded) or item.get("sha256") != hashlib.sha256(encoded).hexdigest():
        return None
    return content


def captured_package_version() -> str | None:
    repo = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "-c", "from importlib.metadata import version; print(version('datamimic_ce'))"],
        cwd=repo,
        env={**os.environ, "PYTHONPATH": str(repo)},
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _at_path(value: Any, path: tuple[str, ...]) -> Any:
    for part in path:
        if isinstance(value, dict) and part in value:
            value = value[part]
        elif isinstance(value, list) and part.isdecimal() and int(part) < len(value):
            value = value[int(part)]
        else:
            return None
    return value


def _set_path(value: dict[str, Any], path: tuple[str, ...], replacement: Any) -> None:
    parent = _at_path(value, path[:-1])
    if isinstance(parent, dict):
        parent[path[-1]] = replacement
    else:
        parent[int(path[-1])] = replacement


def capability_projection_equivalent(old_item: Any, new_item: Any) -> bool:
    old_content, new_content = projection_content(old_item), projection_content(new_item)
    if old_content is None or new_content is None:
        return False
    try:
        old, new = json.loads(old_content), json.loads(new_content)
    except (TypeError, json.JSONDecodeError):
        return False
    if not isinstance(old, dict) or not isinstance(new, dict):
        return False

    # The frozen old value is part of the reviewed snapshot; independently
    # verify the new value against the package installed for this comparison.
    if old.get("schema_version") != _CAPABILITY_OLD_VERSION:
        return False
    if captured_package_version() != new.get("schema_version"):
        return False

    old["schema_version"] = new["schema_version"]
    for path, (before, after) in _CAPABILITY_WORDING_CHANGES.items():
        if _at_path(old, path) != before or _at_path(new, path) != after:
            return False
        _set_path(old, path, _at_path(new, path))
    path, before, after = _CAPABILITY_TRANSITION_CHANGE
    if _at_path(old, path) != before or _at_path(new, path) != after:
        return False
    _set_path(old, path, after)
    return old == new


def projections_equivalent(before: dict[str, Any], after: dict[str, Any]) -> bool:
    required = {"capabilities", "reference_authoring", "reference_scaffold", "compiler"}
    if not required <= before.keys() or before.keys() != after.keys():
        return False
    for name, old_item in before.items():
        new_item = after[name]
        if name == "capabilities":
            if not capability_projection_equivalent(old_item, new_item):
                return False
            continue
        old_content, new_content = projection_content(old_item), projection_content(new_item)
        if old_content is None or new_content is None or old_content != new_content:
            return False
    return True


def canonical_path(path: str) -> str:
    if path.startswith(TARGET_DEMO_PREFIX):
        return LEGACY_DEMO_PREFIX + path.removeprefix(TARGET_DEMO_PREFIX)
    return path


def normalize_evidence(evidence: Any) -> Any:
    if isinstance(evidence, str):
        return _TEST_EVIDENCE_LINE.sub(r"\1:<line>", evidence)
    if isinstance(evidence, list):
        return [normalize_evidence(item) for item in evidence]
    return evidence


def inventory_by_path(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        canonical_path(item["path"]): {
            **item,
            "path": canonical_path(item["path"]),
            **({"evidence": normalize_evidence(item["evidence"])} if "evidence" in item else {}),
        }
        for item in records
    }


def descriptors_by_path(records: dict[str, Any]) -> dict[str, Any]:
    return {canonical_path(path): record for path, record in records.items()}


def comparable(record: dict[str, Any]) -> dict[str, Any]:
    result = {key: record.get(key) for key in ("status", "category", "outcome", "seeded")}
    if record.get("status") == "UNVERIFIED" or record.get("status") == "NOT-A-DESCRIPTOR":
        return {
            **result,
            "reason": record.get("reason"),
            "evidence": normalize_evidence(record.get("evidence")),
        }
    if record.get("outcome") != "ok":
        if record.get("status") == "EXPECTED-ERROR":
            message = record.get("message")
            return {**result, "message": normalize_error_message(message) if isinstance(message, str) else message}
        return {**result, "message": record.get("message"), "stderr": record.get("stderr")}
    if record.get("seeded"):
        return {**result, "result_output_digest": record.get("result_output_digest")}
    return {
        **result,
        "products": record.get("products"),
        "output_files": record.get("output_files"),
        "output_schemas": record.get("output_schemas"),
    }


def shape_compatible(before: Any, after: Any) -> bool:
    if before == "unknown" or after == "unknown" or before == "null" or after == "null":
        return False
    if before == after and not isinstance(before, dict):
        return True
    before_type = before.get("type") if isinstance(before, dict) else None
    after_type = after.get("type") if isinstance(after, dict) else None
    if before_type == "union" or after_type == "union":
        before_values = before.get("values", [before]) if before_type == "union" else [before]
        after_values = after.get("values", [after]) if after_type == "union" else [after]
        before_values = [value for value in before_values if value != "null"]
        after_values = [value for value in after_values if value != "null"]
        if not before_values or not after_values:
            return False
        return all(
            any(shape_compatible(value, candidate) for candidate in candidates)
            for values, candidates in ((before_values, after_values), (after_values, before_values))
            for value in values
        )
    if not isinstance(before, dict) or not isinstance(after, dict):
        return False
    if before_type == after_type == "object":
        before_fields, after_fields = before.get("fields", {}), after.get("fields", {})
        if before_fields.keys() != after_fields.keys():
            return False
        before_presence, after_presence = before.get("presence_counts"), after.get("presence_counts")
        if not isinstance(before_presence, dict) or not isinstance(after_presence, dict):
            return False
        if before_presence.keys() != before_fields.keys() or after_presence.keys() != after_fields.keys():
            return False
        for name in before_fields:
            old_count, new_count = before_presence[name], after_presence[name]
            if not isinstance(old_count, dict) or not isinstance(new_count, dict):
                return False
            old_present, old_total = old_count.get("present"), old_count.get("total")
            new_present, new_total = new_count.get("present"), new_count.get("total")
            if (
                type(old_present) is not int
                or type(new_present) is not int
                or type(old_total) is not int
                or type(new_total) is not int
                or not 0 < old_present <= old_total
                or not 0 < new_present <= new_total
                or (old_present == old_total) != (new_present == new_total)
            ):
                return False
            before_field, after_field = before_fields[name], after_fields[name]
            if not shape_compatible(before_field, after_field):
                return False
        return True
    if before_type == after_type == "array":
        return shape_compatible(before.get("items"), after.get("items"))
    return before == after


def has_nested_array(value: Any, root: bool = True) -> bool:
    if not isinstance(value, dict):
        return False
    kind = value.get("type")
    if kind == "array":
        return not root or has_nested_array(value.get("items"), False)
    if kind == "object":
        return any(has_nested_array(field, False) for field in value.get("fields", {}).values())
    if kind == "union":
        return any(has_nested_array(member, False) for member in value.get("values", []))
    return False


def nested_cardinalities_compatible(
    before_shape: Any,
    after_shape: Any,
    before_counts: Any,
    after_counts: Any,
    before_contract: Any,
    after_contract: Any,
) -> bool:
    before_has_arrays = has_nested_array(before_shape)
    after_has_arrays = has_nested_array(after_shape)
    if before_has_arrays != after_has_arrays:
        return False
    if before_contract != after_contract:
        return False
    if before_contract is not None and (
        not isinstance(before_contract, dict)
        or any(
            not isinstance(path, str) or type(count) is not int or count < 0
            for path, count in before_contract.items()
        )
    ):
        return False
    if not before_has_arrays:
        return before_counts in (None, {}) and after_counts in (None, {})
    if before_contract is None or after_contract is None:
        return False
    if not isinstance(before_counts, dict) or not isinstance(after_counts, dict) or not before_counts:
        return False
    if before_counts.keys() != after_counts.keys():
        return False
    return all(
        isinstance(before_counts[path], list)
        and isinstance(after_counts[path], list)
        and before_counts[path]
        and after_counts[path]
        and all(type(count) is int and count >= 0 for count in before_counts[path])
        and all(type(count) is int and count >= 0 for count in after_counts[path])
        and before_counts[path] == after_counts[path]
        for path in before_counts
    )


def valid_xml_schema(schema: dict[str, Any]) -> bool:
    if set(schema) != {"type", "root", "root_child_count", "element_counts", "elements"}:
        return False
    counts: dict[str, int] = {}

    def valid_element(element: Any, multiplier: int) -> bool:
        if not isinstance(element, dict) or set(element) != {"name", "attributes", "text", "children"}:
            return False
        name, attributes, children = element["name"], element["attributes"], element["children"]
        if (
            not isinstance(name, str) or not name
            or not isinstance(attributes, list)
            or any(not isinstance(attribute, str) or not attribute for attribute in attributes)
            or attributes != sorted(set(attributes))
            or type(element["text"]) is not bool
            or not isinstance(children, list)
        ):
            return False
        counts[name] = counts.get(name, 0) + multiplier
        for child in children:
            if (
                not isinstance(child, dict) or set(child) != {"count", "element"}
                or type(child["count"]) is not int or child["count"] < 1
                or not valid_element(child["element"], multiplier * child["count"])
            ):
                return False
        return True

    root = schema["elements"]
    if not valid_element(root, 1):
        return False
    return (
        schema["type"] == "xml"
        and schema["root"] == root["name"]
        and type(schema["root_child_count"]) is int
        and isinstance(schema["element_counts"], dict)
        and all(
            isinstance(name, str) and name and type(count) is int and count > 0
            for name, count in schema["element_counts"].items()
        )
        and schema["root_child_count"] == sum(child["count"] for child in root["children"])
        and schema["element_counts"] == counts
    )


def equivalent(old: dict[str, Any], new: dict[str, Any]) -> bool:
    allowed_statuses = {"CAPTURED", "EXPECTED-ERROR", "NOT-A-DESCRIPTOR"}
    if any(record.get("status") not in allowed_statuses for record in (old, new)):
        return False
    for record in (old, new):
        if record.get("status") == "CAPTURED":
            if record.get("outcome") != "ok" or type(record.get("seeded")) is not bool:
                return False
            if record["seeded"]:
                digest = record.get("result_output_digest")
                if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                    return False
    for record in (old, new):
        if record.get("status") == "EXPECTED-ERROR" and (
            not isinstance(record.get("outcome"), str)
            or record["outcome"] == "ok"
            or not isinstance(record.get("message"), str)
            or not record["message"].strip()
        ):
            return False
    old_view, new_view = comparable(old), comparable(new)
    if old.get("seeded") or old.get("outcome") != "ok":
        return old_view == new_view
    for key in ("status", "category", "outcome", "seeded", "output_files"):
        if old_view.get(key) != new_view.get(key):
            return False
    before_schemas, after_schemas = old_view.get("output_schemas"), new_view.get("output_schemas")
    before_files, after_files = old_view.get("output_files") or [], new_view.get("output_files") or []
    if not isinstance(before_schemas, dict) or not isinstance(after_schemas, dict):
        return False
    if set(before_schemas) != set(before_files) or set(after_schemas) != set(after_files):
        return False
    if before_schemas.keys() != after_schemas.keys():
        return False
    for path in before_schemas:
        before_schema, after_schema = before_schemas[path], after_schemas[path]
        if not isinstance(before_schema, dict) or not isinstance(after_schema, dict):
            return False
        if before_schema.get("type") == after_schema.get("type") == "xml":
            if (
                not valid_xml_schema(before_schema)
                or not valid_xml_schema(after_schema)
                or before_schema != after_schema
            ):
                return False
        elif (
            before_schema.get("length") != after_schema.get("length")
            or type(before_schema.get("length")) is not int
            or type(after_schema.get("length")) is not int
            or before_schema["length"] < 0
            or after_schema["length"] < 0
            or not shape_compatible(before_schema, after_schema)
            or not nested_cardinalities_compatible(
                before_schema,
                after_schema,
                before_schema.get("nested_cardinalities"),
                after_schema.get("nested_cardinalities"),
                before_schema.get("nested_cardinality_contract"),
                after_schema.get("nested_cardinality_contract"),
            )
        ):
            return False
    before_products, after_products = old.get("products") or {}, new.get("products") or {}
    if before_products.keys() != after_products.keys():
        return False
    return all(
        before_products[name].get("rows") == after_products[name].get("rows")
        and shape_compatible(
            before_products[name].get("value_shape"),
            after_products[name].get("value_shape"),
        )
        and nested_cardinalities_compatible(
            before_products[name].get("value_shape"),
            after_products[name].get("value_shape"),
            before_products[name].get("nested_cardinalities"),
            after_products[name].get("nested_cardinalities"),
            before_products[name].get("nested_cardinality_contract"),
            after_products[name].get("nested_cardinality_contract"),
        )
        for name in before_products
    )


def changed_fields(old: Any, new: Any) -> str:
    if not isinstance(old, dict) or not isinstance(new, dict):
        return "value"
    fields = sorted(key for key in old.keys() | new.keys() if old.get(key) != new.get(key))
    if "products" in fields:
        old_products = old.get("products") or {}
        new_products = new.get("products") or {}
        products = sorted(
            name
            for name in old_products.keys() | new_products.keys()
            if old_products.get(name) != new_products.get(name)
        )
        fields[fields.index("products")] = "products[" + ",".join(products) + "]"
    return ", ".join(fields) or "incomplete evidence"


def self_test() -> None:
    def error(message: str, outcome: str = "ValueError") -> dict[str, Any]:
        return {
            "status": "EXPECTED-ERROR",
            "category": ["intentionally-invalid"],
            "outcome": outcome,
            "seeded": False,
            "message": message,
        }

    first = "Must defined one of following attributes {'pattern', 'generator', 'constant'}"
    reordered = "Must defined one of following attributes {'constant', 'pattern', 'generator'}"
    assert equivalent(error(first), error(reordered))
    assert not equivalent(error(first), error(first.replace("pattern", "regex")))
    assert not equivalent(error(first), error(first, "RuntimeError"))
    assert not equivalent(error(first), error(""))

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("before", nargs="?")
    parser.add_argument("after", nargs="?")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("Step-0 comparator self-test passed")
        return
    if not args.before or not args.after:
        parser.error("before and after snapshot paths are required")
    before, after = load(args.before), load(args.after)
    changed: list[tuple[str, Any, Any]] = []
    tolerated_variances = 0
    for field in ("inventory_count", "category_counts_overlapping"):
        if before.get(field) != after.get(field):
            changed.append((f"inventory.{field}", before.get(field), after.get(field)))
    before_inventory = inventory_by_path(before["inventory"])
    after_inventory = inventory_by_path(after["inventory"])
    for path in sorted(before_inventory.keys() | after_inventory.keys()):
        if before_inventory.get(path) != after_inventory.get(path):
            changed.append((f"inventory.{path}", before_inventory.get(path), after_inventory.get(path)))
    before_descriptors = descriptors_by_path(before["descriptors"])
    after_descriptors = descriptors_by_path(after["descriptors"])
    for path in sorted(before_descriptors.keys() | after_descriptors.keys()):
        old, new = before_descriptors.get(path), after_descriptors.get(path)
        if old is None or new is None or not equivalent(old, new):
            changed.append((f"descriptor.{path}", comparable(old) if old else None, comparable(new) if new else None))
        elif old is not None and new is not None and comparable(old) != comparable(new):
            tolerated_variances += 1
    before_projections = before.get("projections")
    after_projections = after.get("projections")
    projection_pass = False
    if isinstance(before_projections, dict) and isinstance(after_projections, dict):
        projection_pass = projections_equivalent(before_projections, after_projections)
        old_capability = before_projections.get("capabilities")
        new_capability = after_projections.get("capabilities")
        if (
            projection_pass
            and isinstance(old_capability, dict)
            and isinstance(new_capability, dict)
            and old_capability.get("sha256") != new_capability.get("sha256")
        ):
            print(
                "APPROVED Amendment 60 and transition grammar capability projection: "
                f"{old_capability['sha256']} -> {new_capability['sha256']}"
            )
    if not projection_pass:
        changed.append(("projections", before_projections, after_projections))
    print(
        f"{len(before_descriptors)} descriptors compared; {len(changed)} differences; "
        f"{tolerated_variances} normalized or optional-shape variances tolerated"
    )
    for name, old, new in changed:
        print(f"DIFFERENT {name}: {changed_fields(old, new)}")
    if changed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
