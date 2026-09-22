"""Fail when two Step-0 snapshots differ; no descriptor is ignored as flaky."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def comparable(record: dict[str, Any]) -> dict[str, Any]:
    result = {key: record.get(key) for key in ("status", "category", "outcome", "seeded")}
    if record.get("status") == "UNVERIFIED" or record.get("status") == "NOT-A-DESCRIPTOR":
        return {**result, "reason": record.get("reason"), "evidence": record.get("evidence")}
    if record.get("outcome") != "ok":
        if record.get("status") == "EXPECTED-ERROR":
            # Validation text can enumerate an unordered set differently per process.
            return result
        return {**result, "message": record.get("message"), "stderr": record.get("stderr")}
    if record.get("seeded"):
        return {**result, "result_output_digest": record.get("result_output_digest")}
    return {
        **result,
        "products": record.get("products"),
        "output_files": record.get("output_files"),
    }


def shape_compatible(before: Any, after: Any) -> bool:
    if before == after:
        return True
    if before == "unknown" or after == "unknown":
        return True
    before_type = before.get("type") if isinstance(before, dict) else None
    after_type = after.get("type") if isinstance(after, dict) else None
    if before_type == "union" or after_type == "union":
        before_values = before.get("values", [before]) if before_type == "union" else [before]
        after_values = after.get("values", [after]) if after_type == "union" else [after]
        return any(shape_compatible(left, right) for left in before_values for right in after_values)
    if not isinstance(before, dict) or not isinstance(after, dict):
        return False
    if before_type == after_type == "object":
        if "values" in before or "values" in after:
            return "values" in before and "values" in after and shape_compatible(before["values"], after["values"])
        before_fields, after_fields = before.get("fields", {}), after.get("fields", {})
        return all(
            shape_compatible(before_fields[name], after_fields[name])
            for name in before_fields.keys() & after_fields.keys()
        )
    if before_type == after_type == "array":
        return shape_compatible(before.get("items"), after.get("items"))
    return before == after


def equivalent(old: dict[str, Any], new: dict[str, Any]) -> bool:
    old_view, new_view = comparable(old), comparable(new)
    if old.get("seeded") or old.get("outcome") != "ok":
        return old_view == new_view
    for key in ("status", "category", "outcome", "seeded", "output_files"):
        if old_view.get(key) != new_view.get(key):
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
    return ", ".join(fields)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("before")
    parser.add_argument("after")
    args = parser.parse_args()
    before, after = load(args.before), load(args.after)
    changed: list[tuple[str, Any, Any]] = []
    optional_shape_variances = 0
    for field in ("inventory_count", "category_counts_overlapping"):
        if before.get(field) != after.get(field):
            changed.append((f"inventory.{field}", before.get(field), after.get(field)))
    before_inventory = {item["path"]: item for item in before["inventory"]}
    after_inventory = {item["path"]: item for item in after["inventory"]}
    for path in sorted(before_inventory.keys() | after_inventory.keys()):
        if before_inventory.get(path) != after_inventory.get(path):
            changed.append((f"inventory.{path}", before_inventory.get(path), after_inventory.get(path)))
    before_descriptors, after_descriptors = before["descriptors"], after["descriptors"]
    for path in sorted(before_descriptors.keys() | after_descriptors.keys()):
        old, new = before_descriptors.get(path), after_descriptors.get(path)
        if old is None or new is None or not equivalent(old, new):
            changed.append((f"descriptor.{path}", comparable(old) if old else None, comparable(new) if new else None))
        elif old is not None and new is not None and comparable(old) != comparable(new):
            optional_shape_variances += 1
    before_projections = {name: item["sha256"] for name, item in before["projections"].items()}
    after_projections = {name: item["sha256"] for name, item in after["projections"].items()}
    if before_projections != after_projections:
        changed.append(("projections", before_projections, after_projections))
    print(
        f"{len(before_descriptors)} descriptors compared; {len(changed)} differences; "
        f"{optional_shape_variances} optional-shape variances tolerated"
    )
    for name, old, new in changed:
        print(f"DIFFERENT {name}: {changed_fields(old, new)}")
    if changed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
