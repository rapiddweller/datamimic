from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from script.architecture_study.compare_step0 import (
    changed_fields,
    comparable,
    equivalent,
    inventory_by_path,
    shape_compatible,
)
from script.architecture_study.verify_step0 import CHILD, REPO, RESULT_PREFIX, run_descriptor


def test_shape_rejects_missing_object_field() -> None:
    before = {"type": "object", "fields": {"id": "int", "name": "str"}}
    after = {"type": "object", "fields": {"id": "int"}}

    assert not shape_compatible(before, after)


def test_shape_rejects_missing_union_alternative() -> None:
    before = {"type": "union", "values": ["int", "str"]}
    after = {"type": "union", "values": ["int"]}

    assert not shape_compatible(before, after)


def test_shape_rejects_changed_union_member_even_when_both_allow_null() -> None:
    before = {"type": "union", "values": ["int", "null"]}
    after = {"type": "union", "values": ["str", "null"]}

    assert not shape_compatible(before, after)


def test_shape_rejects_unknown_against_concrete_type() -> None:
    assert not shape_compatible("unknown", "int")


def test_shape_accepts_optional_field_presence_variance() -> None:
    before = {
        "type": "object",
        "fields": {"name": "str"},
        "presence_counts": {"name": {"present": 1, "total": 4}},
    }
    after = {
        "type": "object",
        "fields": {"name": "str"},
        "presence_counts": {"name": {"present": 2, "total": 4}},
    }

    assert shape_compatible(before, after)


def test_shape_accepts_nested_optional_field_presence_variance() -> None:
    def shape(car_present: int) -> dict:
        return {
            "type": "object",
            "fields": {
                "pet": {
                    "type": "object",
                    "fields": {
                        "car": {
                            "type": "object",
                            "fields": {"maker": "str"},
                            "presence_counts": {
                                "maker": {"present": car_present, "total": car_present}
                            },
                        }
                    },
                    "presence_counts": {"car": {"present": car_present, "total": 5}},
                }
            },
            "presence_counts": {"pet": {"present": 5, "total": 5}},
        }

    assert shape_compatible(shape(1), shape(2))


@pytest.mark.parametrize(
    ("before_count", "after_count"),
    [(1, 4), (4, 1)],
)
def test_shape_rejects_required_optional_field_change(before_count: int, after_count: int) -> None:
    def shape(present: int) -> dict:
        return {
            "type": "object",
            "fields": {"name": "str"},
            "presence_counts": {"name": {"present": present, "total": 4}},
        }

    assert not shape_compatible(shape(before_count), shape(after_count))


@pytest.mark.parametrize(
    ("present", "total"),
    [(0, 4), (5, 4), (1.5, 4), (1, 0)],
)
def test_shape_rejects_invalid_presence_counts(present: int | float, total: int) -> None:
    invalid_shape = {
        "type": "object",
        "fields": {"name": "str"},
        "presence_counts": {"name": {"present": present, "total": total}},
    }

    assert not shape_compatible(invalid_shape, invalid_shape)


def test_shape_does_not_accept_legacy_object_without_presence_metadata() -> None:
    legacy_shape = {"type": "object", "fields": {"id": "int"}}

    assert not shape_compatible(legacy_shape, legacy_shape)


def test_shape_does_not_accept_incomplete_presence_metadata() -> None:
    incomplete_shape = {
        "type": "object",
        "fields": {"id": "int", "name": "str"},
        "presence_counts": {"id": {"present": 2, "total": 2}},
    }

    assert not shape_compatible(incomplete_shape, incomplete_shape)


def test_shape_does_not_accept_legacy_object_values_without_presence_metadata() -> None:
    legacy_map_shape = {"type": "object", "values": "int"}

    assert not shape_compatible(legacy_map_shape, legacy_map_shape)


def test_shape_accepts_null_sample_when_field_and_concrete_type_remain() -> None:
    before = {
        "type": "object",
        "fields": {"nickname": {"type": "union", "values": ["int", "null"]}},
        "presence_counts": {"nickname": {"present": 2, "total": 2}},
    }
    after = {
        "type": "object",
        "fields": {"nickname": "int"},
        "presence_counts": {"nickname": {"present": 2, "total": 2}},
    }

    assert shape_compatible(before, after)


def test_shape_does_not_accept_all_null_against_concrete_type() -> None:
    before = {
        "type": "object",
        "fields": {"nickname": "null"},
        "presence_counts": {"nickname": {"present": 2, "total": 2}},
    }
    after = {
        "type": "object",
        "fields": {"nickname": "int"},
        "presence_counts": {"nickname": {"present": 2, "total": 2}},
    }

    assert not shape_compatible(before, after)


def test_shape_does_not_accept_identical_all_null_field_as_structural_proof() -> None:
    all_null_shape = {
        "type": "object",
        "fields": {"nickname": "null"},
        "presence_counts": {"nickname": {"present": 2, "total": 2}},
    }

    assert not shape_compatible(all_null_shape, all_null_shape)


def test_child_records_actual_rows_for_dynamic_count(tmp_path: Path) -> None:
    descriptor = tmp_path / "count_expression.xml"
    shutil.copy2(REPO / "tests_ce/integration_tests/test_count_expression/count_expression.xml", descriptor)
    env = {**os.environ, "PYTHONPATH": str(REPO)}
    result = subprocess.run(
        [sys.executable, "-c", CHILD, str(descriptor)],
        cwd=REPO,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )

    record_line = next(line for line in result.stdout.splitlines() if line.startswith(RESULT_PREFIX))
    record = json.loads(record_line.removeprefix(RESULT_PREFIX))
    assert record["outcome"] == "ok"
    assert record["products"]["orders"]["rows"] == 12
    assert record["products"]["orders"]["value_shape"]["presence_counts"]["i"] == {
        "present": 12,
        "total": 12,
    }


def test_child_capture_and_comparison_reject_nested_field_removal(tmp_path: Path) -> None:
    descriptor = tmp_path / "nested.xml"
    descriptor.write_text(
        '<setup><generate name="orders" count="2" target="">'
        '<key name="order_id" generator="IncrementGenerator"/>'
        '<nestedKey name="items" type="list" count="2">'
        '<key name="line_no" generator="IncrementGenerator"/>'
        '<key name="amount" type="int" min="10" max="20"/>'
        "</nestedKey></generate></setup>",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-c", CHILD, str(descriptor)],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(REPO)},
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )

    record_line = next(line for line in result.stdout.splitlines() if line.startswith(RESULT_PREFIX))
    record = json.loads(record_line.removeprefix(RESULT_PREFIX))
    shape = record["products"]["orders"]["value_shape"]
    item_shape = shape["fields"]["items"]["items"]
    assert set(item_shape["fields"]) == {"amount", "line_no"}

    changed_shape = copy.deepcopy(shape)
    del changed_shape["fields"]["items"]["items"]["fields"]["line_no"]
    assert not shape_compatible(shape, changed_shape)


@pytest.mark.parametrize(
    ("chunk_size", "root_type", "file_count"), [(None, "array", 1), (1, "object", 2)]
)
def test_child_captures_json_output_schema_for_list_and_object_roots(
    tmp_path: Path, chunk_size: int | None, root_type: str, file_count: int
) -> None:
    source = REPO / "tests_ce/integration_tests/test_export_uri/json_uri.xml"
    descriptor = tmp_path / source.name
    root = ET.parse(source).getroot()
    if chunk_size is not None:
        root.find("generate").set("target", f"JSON(chunk_size={chunk_size})")
    ET.ElementTree(root).write(descriptor, encoding="unicode")
    result = subprocess.run(
        [sys.executable, "-c", CHILD, str(descriptor)],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(REPO)},
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )

    record_line = next(line for line in result.stdout.splitlines() if line.startswith(RESULT_PREFIX))
    record = json.loads(record_line.removeprefix(RESULT_PREFIX))
    schemas = record["output_schemas"]
    assert len(schemas) == file_count
    for file_shape in schemas.values():
        assert file_shape["type"] == root_type
        row_shape = file_shape["items"] if root_type == "array" else file_shape
        assert row_shape["fields"] == {"n": "str"}


def test_unseeded_xml_capture_records_expanded_tags_and_child_order(tmp_path: Path) -> None:
    source = REPO / "tests_ce/integration_tests/consumer_xml/test_generate_single_item_xml.xml"
    descriptor = tmp_path / source.name
    shutil.copy2(source, descriptor)

    _, record = run_descriptor(
        {"path": str(descriptor), "category": ["runnable"], "evidence": []}
    )

    assert record["status"] == "CAPTURED"
    assert record["output_schema_expected"] is True
    schema = record["output_schemas"]["xml_single_item.xml"]
    assert schema["type"] == "xml"
    assert schema["root"] == "{http://example.com/course}course"
    root_children = schema["elements"]["children"]
    assert [child["element"]["name"] for child in root_children] == [
        "{http://example.com/course}title",
        "{http://example.com/chapter}chapter",
    ]
    chapter = root_children[1]["element"]
    assert chapter["name"] == "{http://example.com/chapter}chapter"
    assert [child["element"]["name"] for child in chapter["children"]] == [
        "{http://example.com/chapter}title",
        "{http://example.com/lesson}lesson",
    ]


def _unseeded_json_record(schema: dict[str, object] | None) -> dict[str, object]:
    record: dict[str, object] = {
        "status": "CAPTURED",
        "category": ["runnable"],
        "outcome": "ok",
        "seeded": False,
        "products": {
            "rows": {
                "rows": 1,
                "value_shape": {
                    "type": "object",
                    "fields": {"n": "str"},
                    "presence_counts": {"n": {"present": 1, "total": 1}},
                },
            }
        },
        "output_files": ["rows.json" if schema is not None else "rows.txt"],
    }
    if schema is not None:
        record["output_schemas"] = {record["output_files"][0]: schema}
    return record


def test_unseeded_comparison_rejects_deleted_json_output_field() -> None:
    before_schema = {
        "type": "array",
        "items": {
            "type": "object",
            "fields": {"n": "str"},
            "presence_counts": {"n": {"present": 1, "total": 1}},
        },
        "length": 1,
    }
    after_schema = {
        "type": "array",
        "items": {"type": "object", "fields": {}, "presence_counts": {}},
        "length": 1,
    }

    baseline = _unseeded_json_record(before_schema)
    assert equivalent(baseline, baseline)
    assert not equivalent(_unseeded_json_record(before_schema), _unseeded_json_record(after_schema))


def _xml_output_record(schema: dict[str, object] | None) -> dict[str, object]:
    record: dict[str, object] = {
        "status": "CAPTURED",
        "category": ["runnable"],
        "outcome": "ok",
        "seeded": False,
        # The in-memory product capture is deliberately identical across XML variants.
        "products": {
            "rows": {
                "rows": 2,
                "value_shape": {
                    "type": "object",
                    "fields": {"n": "str"},
                    "presence_counts": {"n": {"present": 2, "total": 2}},
                },
            }
        },
        "output_files": ["rows.xml"],
    }
    if schema is not None:
        record["output_schemas"] = {"rows.xml": schema}
    return record


def _xml_schema(
    *, root: str = "{urn:rows}rows", child: str = "{urn:rows}row",
    attribute: str = "id", child_order: tuple[str, ...] | None = None, record_count: int = 2,
) -> dict[str, object]:
    child_order = child_order or ("{urn:rows}id", "{urn:rows}name")
    return {
        "type": "xml",
        "root": root,
        "root_child_count": record_count,
        "element_counts": {root: 1, child: record_count, **{tag: record_count for tag in child_order}},
        "elements": {
            "name": root,
            "attributes": [],
            "text": False,
            "children": [
                {
                    "count": record_count,
                    "element": {
                        "name": child,
                        "attributes": [attribute],
                        "text": False,
                        "children": [
                            {
                                "count": 1,
                                "element": {"name": tag, "attributes": [], "text": True, "children": []},
                            }
                            for tag in child_order
                        ],
                    },
                }
            ],
        },
    }


def test_unseeded_xml_comparison_ignores_text_values_but_keeps_structure() -> None:
    schema = _xml_schema()

    assert equivalent(_xml_output_record(schema), _xml_output_record(copy.deepcopy(schema)))


@pytest.mark.parametrize(
    "changed_schema",
    [
        _xml_schema(child="{urn:rows}other"),
        _xml_schema(attribute="key"),
        _xml_schema(root="{urn:other}rows"),
        _xml_schema(child_order=("{urn:rows}name", "{urn:rows}id")),
        _xml_schema(record_count=1),
    ],
    ids=["child-removal", "attribute-removal", "namespace-tag", "child-order", "record-count"],
)
def test_unseeded_xml_comparison_rejects_structural_export_changes(
    changed_schema: dict[str, object],
) -> None:
    assert not equivalent(_xml_output_record(_xml_schema()), _xml_output_record(changed_schema))


def test_unseeded_xml_comparison_rejects_swapped_children_across_same_tag_siblings() -> None:
    def sibling(attribute: str, child: str) -> dict[str, object]:
        return {
            "name": "{urn:rows}row",
            "attributes": [attribute],
            "text": False,
            "children": [
                {
                    "count": 1,
                    "element": {"name": child, "attributes": [], "text": True, "children": []},
                }
            ],
        }

    def schema(rows: list[dict[str, object]]) -> dict[str, object]:
        return {
            "type": "xml",
            "root": "{urn:rows}rows",
            "root_child_count": 2,
            "element_counts": {
                "{urn:rows}rows": 1,
                "{urn:rows}row": 2,
                "{urn:rows}left": 1,
                "{urn:rows}right": 1,
            },
            "elements": {
                "name": "{urn:rows}rows",
                "attributes": [],
                "text": False,
                "children": [{"count": 1, "element": row} for row in rows],
            },
        }

    original = schema([sibling("left-id", "{urn:rows}left"), sibling("right-id", "{urn:rows}right")])
    swapped = schema([sibling("left-id", "{urn:rows}right"), sibling("right-id", "{urn:rows}left")])

    assert not equivalent(_xml_output_record(original), _xml_output_record(swapped))


def test_unseeded_xml_comparison_requires_existing_well_formed_schema_evidence() -> None:
    baseline = _xml_output_record(_xml_schema())
    no_schema = _xml_output_record(None)
    malformed_schema = _xml_output_record({"type": "xml", "elements": "not-an-element-map"})
    missing_file = copy.deepcopy(baseline)
    missing_file["output_files"] = []

    assert not equivalent(baseline, no_schema)
    assert not equivalent(baseline, malformed_schema)
    assert not equivalent(malformed_schema, malformed_schema)
    assert not equivalent(baseline, missing_file)


def test_unseeded_xml_comparison_rejects_boolean_as_element_count() -> None:
    malformed = _xml_schema(record_count=1)
    malformed["root_child_count"] = True
    malformed["element_counts"]["{urn:rows}rows"] = True
    record = _xml_output_record(malformed)

    assert not equivalent(record, record)


def test_seeded_xml_capture_still_requires_exact_output_digest() -> None:
    before = {
        "status": "CAPTURED", "category": ["runnable"], "outcome": "ok", "seeded": True,
        "result_output_digest": "a" * 64,
    }
    after = {**before, "result_output_digest": "b" * 64}

    assert equivalent(before, before)
    assert not equivalent(before, after)


def test_unseeded_comparison_rejects_deleted_nested_json_key() -> None:
    before_schema = {
        "type": "object",
        "fields": {
            "payload": {
                "type": "object",
                "fields": {"child_id": "str"},
                "presence_counts": {"child_id": {"present": 1, "total": 1}},
            }
        },
        "presence_counts": {"payload": {"present": 1, "total": 1}},
        "length": 1,
    }
    after_schema = {
        "type": "object",
        "fields": {"payload": {"type": "object", "fields": {}, "presence_counts": {}}},
        "presence_counts": {"payload": {"present": 1, "total": 1}},
        "length": 1,
    }

    baseline = _unseeded_json_record(before_schema)
    assert equivalent(baseline, baseline)
    assert not equivalent(_unseeded_json_record(before_schema), _unseeded_json_record(after_schema))


def test_unseeded_comparison_requires_schema_for_unsupported_text_output() -> None:
    incomplete = _unseeded_json_record(None)

    assert not equivalent(incomplete, incomplete)
    assert changed_fields(comparable(incomplete), comparable(incomplete)) == "incomplete evidence"


def test_identical_unverified_service_record_is_not_parity_proof() -> None:
    unverified = {
        "status": "UNVERIFIED",
        "category": ["runnable", "external-service"],
        "reason": "UNVERIFIED: service inventory unavailable",
        "evidence": ["tests_ce/external_service_tests/test_db.py"],
    }

    assert not equivalent(unverified, unverified)


@pytest.mark.parametrize(
    "status", ["UNRUNNABLE", "UNEXPECTED-SUCCESS"],
)
def test_identical_non_success_status_is_not_parity_proof(status: str) -> None:
    record = {
        "status": status,
        "category": ["runnable"],
        "outcome": "ok" if status == "UNEXPECTED-SUCCESS" else "timeout",
        "seeded": status == "UNEXPECTED-SUCCESS",
        "result_output_digest": "same" if status == "UNEXPECTED-SUCCESS" else None,
    }

    assert not equivalent(record, record)


@pytest.mark.parametrize("digest", [None, ""])
def test_seeded_capture_requires_nonempty_output_digest(digest: str | None) -> None:
    record = {
        "status": "CAPTURED",
        "category": ["runnable"],
        "outcome": "ok",
        "seeded": True,
        "result_output_digest": digest,
    }

    assert not equivalent(record, record)


@pytest.mark.parametrize("outcome", [None, "timeout"])
def test_captured_record_requires_ok_outcome(outcome: str | None) -> None:
    record = {
        "status": "CAPTURED",
        "category": ["runnable"],
        "outcome": outcome,
        "seeded": False,
    }

    assert not equivalent(record, record)


def test_unseeded_ndjson_capture_is_unverified_without_schema(tmp_path: Path) -> None:
    source = REPO / "tests_ce/integration_tests/test_export_uri/json_uri.xml"
    descriptor = tmp_path / source.name
    root = ET.parse(source).getroot()
    root.find("generate").set("target", "JSON(use_ndjson=True)")
    ET.ElementTree(root).write(descriptor, encoding="unicode")

    _, record = run_descriptor(
        {"path": str(descriptor), "category": ["runnable"], "evidence": []}
    )

    assert record["status"] == "UNVERIFIED"
    assert "schema" in record["reason"].lower()
    assert not equivalent(record, record)


def test_empty_json_array_export_is_unverified_without_concrete_schema(tmp_path: Path) -> None:
    source = REPO / "tests_ce/integration_tests/test_export_uri/json_uri.xml"
    descriptor = tmp_path / source.name
    root = ET.parse(source).getroot()
    root.find("generate").set("count", "0")
    ET.ElementTree(root).write(descriptor, encoding="unicode")

    _, record = run_descriptor(
        {"path": str(descriptor), "category": ["runnable"], "evidence": []}
    )

    assert record["status"] == "UNVERIFIED"
    assert "schema" in record["reason"].lower()


def test_zero_row_configured_json_export_is_unverified_without_file(tmp_path: Path) -> None:
    source = REPO / "tests_ce/integration_tests/test_export_uri/json_uri.xml"
    descriptor = tmp_path / source.name
    root = ET.parse(source).getroot()
    generate = root.find("generate")
    generate.set("count", "0")
    generate.set("target", "JSON(chunk_size=1)")
    ET.ElementTree(root).write(descriptor, encoding="unicode")

    _, record = run_descriptor(
        {"path": str(descriptor), "category": ["runnable"], "evidence": []}
    )

    assert record["status"] == "UNVERIFIED"
    assert "schema" in record["reason"].lower()


def test_nested_empty_json_array_export_is_unverified(tmp_path: Path) -> None:
    descriptor = tmp_path / "nested_empty.xml"
    descriptor.write_text(
        '<setup><generate name="rows" count="1" target="JSON" exportUri="out">'
        '<key name="id" generator="IncrementGenerator"/>'
        '<nestedKey name="items" type="list" count="0">'
        '<key name="value" constant="x"/>'
        "</nestedKey></generate></setup>",
        encoding="utf-8",
    )

    _, record = run_descriptor(
        {"path": str(descriptor), "category": ["runnable"], "evidence": []}
    )

    assert record["status"] == "UNVERIFIED"
    assert "schema" in record["reason"].lower()


def test_all_null_json_field_export_is_unverified(tmp_path: Path) -> None:
    descriptor = tmp_path / "all_null.xml"
    (tmp_path / "input.json").write_text('[{"id": null}]', encoding="utf-8")
    descriptor.write_text(
        '<setup><generate name="rows" source="input.json" count="1" '
        'target="JSON" exportUri="out" distribution="ordered"/></setup>',
        encoding="utf-8",
    )

    _, record = run_descriptor(
        {"path": str(descriptor), "category": ["runnable"], "evidence": []}
    )

    assert record["status"] == "UNVERIFIED"
    assert "schema" in record["reason"].lower()


def test_unseeded_json_output_schema_rejects_row_loss() -> None:
    before = _unseeded_json_record(
        {
            "type": "array",
            "items": {
                "type": "object",
                "fields": {"n": "str"},
                "presence_counts": {"n": {"present": 1, "total": 1}},
            },
            "length": 2,
        }
    )
    after = _unseeded_json_record(
        {
            "type": "array",
            "items": {
                "type": "object",
                "fields": {"n": "str"},
                "presence_counts": {"n": {"present": 1, "total": 1}},
            },
            "length": 1,
        }
    )
    # Product results are held constant to prove the exported file itself is checked.
    before["products"] = after["products"]

    assert not equivalent(before, after)


def test_child_rejects_import_outside_its_pythonpath_root(tmp_path: Path) -> None:
    descriptor = tmp_path / "safe.xml"
    descriptor.write_text(
        '<setup><generate name="items" count="1" target="">'
        '<key name="id" generator="IncrementGenerator"/>'
        "</generate></setup>",
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": str(tmp_path / "empty-pythonpath")}
    (tmp_path / "empty-pythonpath").mkdir()
    result = subprocess.run(
        [sys.executable, "-c", CHILD, str(descriptor)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    output = result.stdout + result.stderr
    assert result.returncode != 0 or RESULT_PREFIX not in result.stdout
    assert "PYTHONPATH" in output or "import root" in output.lower()


def test_evidence_line_moves_are_ignored_by_inventory_and_comparable() -> None:
    before_evidence = [
        "tests_ce/test_rows.py:10 tests orders; assertions at tests_ce/test_rows.py:14"
    ]
    after_evidence = [
        "tests_ce/test_rows.py:20 tests orders; assertions at tests_ce/test_rows.py:24"
    ]
    before = {"path": "tests_ce/orders.xml", "category": ["runnable"], "evidence": before_evidence}
    after = {"path": "tests_ce/orders.xml", "category": ["runnable"], "evidence": after_evidence}

    assert inventory_by_path([before]) == inventory_by_path([after])
    assert comparable({**before, "status": "UNVERIFIED"}) == comparable(
        {**after, "status": "UNVERIFIED"}
    )


def test_evidence_normalization_preserves_test_path_and_semantics() -> None:
    evidence = "tests_ce/test_rows.py:10 tests orders; assertions at tests_ce/test_rows.py:14"
    baseline = {"path": "tests_ce/orders.xml", "category": ["runnable"], "evidence": [evidence]}
    changed_path = {**baseline, "evidence": [evidence.replace("test_rows.py", "test_other.py")]}
    changed_semantics = {**baseline, "evidence": [evidence.replace("tests orders", "tests users")]}

    assert inventory_by_path([baseline]) != inventory_by_path([changed_path])
    assert inventory_by_path([baseline]) != inventory_by_path([changed_semantics])
    for changed in (changed_path, changed_semantics):
        assert comparable({**baseline, "status": "UNVERIFIED"}) != comparable(
            {**changed, "status": "UNVERIFIED"}
        )
