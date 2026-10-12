"""Capture descriptor behavior and canonical authoring projections at Step 0.

Run with the project interpreter:
    .venv/bin/python script/architecture_study/verify_step0.py /tmp/step0.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
TIMEOUT_SECONDS = 180
CAPABILITIES_SHA256 = "b068f56ea06710d1f26a8b3a27fb1faafdfe52fd6a7ee2c180587c6279831496"
AUTHORING_REFERENCE_SHA256 = "7c99444c15b8a869c4b1b213c758488042ef8cd84ca559dd4e91b2da4a2778f1"
RESULT_PREFIX = "STEP0_RESULT "
CHILD = r"""
import hashlib, json, os, sys, zipfile
from pathlib import Path
from datetime import date, datetime, time
from decimal import Decimal
import xml.etree.ElementTree as ET
roots = os.environ.get("PYTHONPATH", "").split(os.pathsep)
if len(roots) != 1 or not roots[0]:
    raise RuntimeError("import root mismatch: expected one PYTHONPATH checkout root")
checkout_root = Path(roots[0]).resolve()
import datamimic_ce
try:
    Path(datamimic_ce.__file__).resolve().relative_to((checkout_root / "datamimic_ce").resolve())
except ValueError:
    raise RuntimeError("import root mismatch: datamimic_ce loaded outside the checkout root") from None
if (checkout_root / "datamimic_ce/interfaces/python/data_mimic_test.py").is_file():
    from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest
    from datamimic_ce.engine.dsl.statements.generation.targets import parse_consumer
else:
    from datamimic_ce.data_mimic_test import DataMimicTest
    from datamimic_ce.engine.dsl.statements.statement_util import StatementUtil
    parse_consumer = StatementUtil.parse_consumer

def normalize(item):
    if item is None or isinstance(item, (bool, int, str)):
        return item
    if isinstance(item, float):
        return {"type": "float", "value": item.hex()}
    if isinstance(item, Decimal):
        return {"type": "decimal", "value": str(item)}
    if isinstance(item, (datetime, date, time)):
        return {"type": type(item).__name__, "value": item.isoformat()}
    if isinstance(item, bytes):
        return {"type": "bytes", "value": __import__("base64").b64encode(item).decode("ascii")}
    if isinstance(item, dict):
        return {str(key): normalize(value) for key, value in sorted(item.items(), key=lambda pair: str(pair[0]))}
    if isinstance(item, (list, tuple)):
        return [normalize(value) for value in item]
    if isinstance(item, set):
        items = [normalize(value) for value in item]
        return sorted(items, key=lambda item: json.dumps(item, sort_keys=True, default=str))
    return {"type": type(item).__qualname__, "value": str(item)}

def shape(item):
    if isinstance(item, dict):
        return {
            "type": "object",
            "fields": {key: shape(value) for key, value in sorted(item.items())},
            "presence_counts": {key: {"present": 1, "total": 1} for key in item},
        }
    if isinstance(item, list):
        return {"type": "array", "items": shape_union(item)}
    if item is None:
        return "null"
    if isinstance(item, bool):
        return "bool"
    if isinstance(item, int):
        return "int"
    if isinstance(item, float):
        return "float"
    return type(item).__name__

def shape_union(items):
    if not items:
        return "unknown"
    if items and all(isinstance(value, list) for value in items):
        members = [member for value in items for member in value]
        return {"type": "array", "items": shape_union(members) if members else "unknown"}
    if items and all(isinstance(value, dict) for value in items):
        keys = sorted({key for value in items for key in value})
        return {
            "type": "object",
            "fields": {
                key: shape_union([value[key] for value in items if key in value])
                for key in keys
            },
            "presence_counts": {
                key: {"present": sum(key in value for value in items), "total": len(items)}
                for key in keys
            },
        }
    members = sorted({json.dumps(shape(value), sort_keys=True) for value in items})
    if len(members) == 1:
        return json.loads(members[0])
    return {"type": "union", "values": [json.loads(value) for value in members]}

def complete_shape(value):
    if value == "unknown" or value == "null":
        return False
    if not isinstance(value, dict):
        return True
    kind = value.get("type")
    if kind == "union":
        members = [member for member in value.get("values", []) if member != "null"]
        return bool(members) and all(complete_shape(member) for member in members)
    if kind == "array":
        return complete_shape(value.get("items"))
    if kind == "object":
        fields, presence = value.get("fields"), value.get("presence_counts")
        return (
            isinstance(fields, dict)
            and isinstance(presence, dict)
            and fields.keys() == presence.keys()
            and all(complete_shape(field) for field in fields.values())
        )
    return False

def shape_rows(rows):
    if not isinstance(rows, list) or not rows:
        return shape(rows)
    return shape_union(rows)

def nested_cardinalities(value):
    counts = {}

    def visit(item, path):
        if isinstance(item, list):
            if path:
                counts.setdefault(path, []).append(len(item))
            for child in item:
                visit(child, path + "/*")
        elif isinstance(item, dict):
            for key, child in item.items():
                escaped = str(key).replace("~", "~0").replace("/", "~1")
                visit(child, path + "/" + escaped)

    if isinstance(value, list):
        for row in value:
            visit(row, "")
    else:
        visit(value, "")
    return {path: sorted(lengths) for path, lengths in sorted(counts.items())}

def xml_element_shape(element):
    children = []
    for child in element:
        child_shape = xml_element_shape(child)
        if children and children[-1]["element"] == child_shape:
            children[-1]["count"] += 1
        else:
            children.append({"count": 1, "element": child_shape})
    return {
        "name": element.tag,
        "attributes": sorted(element.attrib),
        "text": bool((element.text or "").strip()),
        "children": children,
    }

def xml_shape(path):
    root = ET.parse(path).getroot()
    element_counts = {}
    for element in root.iter():
        element_counts[element.tag] = element_counts.get(element.tag, 0) + 1
    return {
        "type": "xml",
        "root": root.tag,
        "root_child_count": len(root),
        "element_counts": dict(sorted(element_counts.items())),
        "elements": xml_element_shape(root),
    }

def output_digest(path):
    if path.suffix == ".xlsx":
        # OOXML core properties include the current creation/modification time.
        with zipfile.ZipFile(path) as archive:
            entries = {
                name: hashlib.sha256(archive.read(name)).hexdigest()
                for name in sorted(archive.namelist())
                if name != "docProps/core.xml"
            }
        return hashlib.sha256(json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return hashlib.sha256(path.read_bytes()).hexdigest()

path = Path(sys.argv[1])
seeded = False
task_id = None
try:
    seeded = "rngSeed" in ET.parse(path).getroot().attrib
    engine = DataMimicTest(test_dir=path.parent, filename=path.name, capture_test_result=True)
    task_id = engine.task_id
    engine.test_with_timer()
    result = engine.capture_result()
    expected_output_formats = sorted({
        {"JSON": "json", "XML": "xml", "DbUnit": "dbunit.xml"}[consumer.partition("(")[0]]
        for node in ET.parse(path).getroot().iter("generate")
        for consumer in parse_consumer(node.get("target"))
        if consumer.partition("(")[0] in {"JSON", "XML", "DbUnit"}
    })
    expects_structural_output = bool(expected_output_formats)
    if seeded:
        normalized = normalize(result)
        canonical = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        record = {"outcome": "ok", "seeded": True, "result_digest": hashlib.sha256(canonical.encode()).hexdigest()}
    else:
        products = result or {}
        record = {
            "outcome": "ok", "seeded": False,
            "products": {
                name: {
                    "rows": len(rows) if isinstance(rows, list) else 1,
                    "value_shape": shape_rows(rows),
                    "nested_cardinalities": nested_cardinalities(rows),
                }
                for name, rows in sorted(products.items())
            },
        }
    output = path.parent / "output"
    files = {}
    output_schemas = {}
    if output.is_dir():
        for item in sorted(output.rglob("*")):
            if item.is_file():
                relative = item.relative_to(output)
                if task_id is not None and relative.parts[0] == task_id:
                    relative = Path(*relative.parts[1:])
                files[str(relative)] = output_digest(item)
                if not seeded and item.suffix == ".json":
                    try:
                        with item.open(encoding="utf-8") as exported_file:
                            payload = json.load(exported_file)
                        if isinstance(payload, (dict, list)):
                            output_shape = shape(payload)
                            if complete_shape(output_shape):
                                output_shape["length"] = len(payload) if isinstance(payload, list) else 1
                                output_shape["nested_cardinalities"] = nested_cardinalities(payload)
                                output_schemas[str(relative)] = output_shape
                    except (OSError, UnicodeError, json.JSONDecodeError):
                        pass
                elif not seeded and item.suffix == ".xml":
                    output_shape = xml_shape(item)
                    output_schemas[str(relative)] = output_shape
    record["output_files"] = files if seeded else sorted(files)
    if seeded:
        record["output_digest"] = hashlib.sha256(
            json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        result_and_output = {"result": record["result_digest"], "output": files}
        record["result_output_digest"] = hashlib.sha256(
            json.dumps(
                result_and_output, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode()
        ).hexdigest()
    else:
        record["output_schemas"] = output_schemas
        record["output_schema_expected"] = expects_structural_output
        record["output_schema_expected_formats"] = expected_output_formats
except Exception as error:
    record = {
        "outcome": type(error).__name__, "seeded": seeded,
        "message": str(error).replace(str(path.parent), "<descriptor-dir>").replace(
            os.environ["PYTHONPATH"], "<checkout>"
        ),
    }
print("STEP0_RESULT " + json.dumps(record, sort_keys=True, ensure_ascii=False, default=str), flush=True)
"""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def descriptor_generate_counts(path: Path) -> dict[str, str | None]:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return {}
    return {
        node.get("name"): node.get("count")
        for node in root.iter("generate")
        if node.get("name") is not None
    }


def nested_list_count_contract(path: Path) -> tuple[dict[str, dict[str, int]], set[str], bool, bool]:
    root = ET.parse(path).getroot()
    contracts: dict[str, dict[str, int]] = {}
    uncertain_products: set[str] = set()
    visited: set[int] = set()
    generates = root.findall("./generate")
    names = [node.get("name") for node in generates]
    duplicate_products = {name for name in names if name is not None and names.count(name) > 1}

    def visit(parent: ET.Element, prefix: str, parent_known: bool, expected: dict[str, int]) -> bool:
        uncertain = False
        children = list(parent)
        child_names = [child.get("name") for child in children]
        duplicate_names = {name for name in child_names if name is not None and child_names.count(name) > 1}
        for child in children:
            if child.tag == "nestedKey":
                visited.add(id(child))
                name = child.get("name")
                if name is None:
                    uncertain = True
                    continue
                escaped = name.replace("~", "~0").replace("/", "~1")
                field_path = prefix + "/" + escaped
                nested_type = child.get("type")
                if nested_type == "list":
                    count = child.get("count", "")
                    fixed = (
                        parent_known
                        and name not in duplicate_names
                        and count.isdigit()
                        and child.get("source") is None
                        and child.get("script") is None
                        and child.get("condition") is None
                        and child.get("converter") is None
                        and child.get("minCount") is None
                        and child.get("maxCount") is None
                        and child.get("defaultValue") is None
                    )
                    if fixed:
                        expected[field_path] = int(count)
                    else:
                        uncertain = True
                    uncertain = visit(child, field_path + "/*", fixed, expected) or uncertain
                elif nested_type == "dict":
                    known = (
                        parent_known
                        and name not in duplicate_names
                        and child.get("source") is None
                        and child.get("script") is None
                        and child.get("condition") is None
                    )
                    uncertain = visit(child, field_path, known, expected) or uncertain
                else:
                    uncertain = visit(child, field_path, False, expected) or uncertain
            elif list(child):
                # Control-flow or another unnamed container can change whether a list field exists.
                uncertain = visit(child, prefix, False, expected) or uncertain
        return uncertain

    for node in generates:
        name = node.get("name")
        if name is None:
            continue
        expected: dict[str, int] = {}
        uncertain = visit(node, "", name not in duplicate_products, expected)
        if name in duplicate_products:
            uncertain = True
        contracts[name] = expected
        if uncertain:
            uncertain_products.add(name)

    unvisited_list = any(
        node.tag == "nestedKey" and node.get("type") == "list" and id(node) not in visited
        for node in root.iter("nestedKey")
    )
    direct_generates = {id(node) for node in generates}
    unknown_scope = any(id(node) not in direct_generates for node in root.iter("generate")) or any(
        Path(node.get("uri", "")).suffix.lower() != ".properties" for node in root.iter("include")
    )
    return contracts, uncertain_products, unvisited_list, unknown_scope


def matches_nested_cardinalities(observed: Any, expected: dict[str, int], root_count: int) -> bool:
    if not isinstance(observed, dict) or type(root_count) is not int or root_count < 0:
        return False
    if not observed.keys() <= expected.keys():
        return False

    def occurrence_count(path: str) -> int | None:
        if "/*/" not in path:
            return root_count
        parent_path = path.rsplit("/*/", 1)[0]
        parent_count = expected.get(parent_path)
        parent_occurrences = occurrence_count(parent_path)
        return None if parent_count is None or parent_occurrences is None else parent_count * parent_occurrences

    for path, count in expected.items():
        occurrences = occurrence_count(path)
        lengths = observed.get(path)
        if occurrences is None:
            return False
        if occurrences == 0:
            if lengths is not None:
                return False
        elif (
            not isinstance(lengths, list)
            or len(lengths) != occurrences
            or any(type(length) is not int or length != count for length in lengths)
        ):
            return False
    return True


def test_evidence(path: Path) -> str | None:
    filename = path.name
    for source in sorted(path.parent.glob("*.py")):
        lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
        for index, line in enumerate(lines):
            if filename not in line:
                continue
            start = index
            while start > 0 and not re.match(r"\s*def test_", lines[start]):
                start -= 1
            end = index + 1
            while end < len(lines) and not re.match(r"\s*def test_", lines[end]):
                end += 1
            execution = next(
                (
                    position
                    for position in range(index, end)
                    if re.search(r"(?:test_with_timer|parse_and_execute|_run)\s*\(", lines[position])
                ),
                None,
            )
            if execution is None:
                continue
            call_indent = len(lines[execution]) - len(lines[execution].lstrip())
            guarded = any(
                re.search(r"pytest\.raises|assertRaises", lines[position])
                and len(lines[position]) - len(lines[position].lstrip()) < call_indent
                for position in range(start, execution + 1)
            )
            if guarded:
                return f"{source.relative_to(REPO)}:{start + 1} references {filename} and asserts an error"
    return None


def missing_xlsx_source_evidence(path: Path, root: ET.Element) -> list[str]:
    generated: set[str] = set()
    missing: set[str] = set()
    for node in root.iter():
        source = node.get("source")
        if (
            source
            and Path(source).suffix.lower() == ".xlsx"
            and not (path.parent / source).is_file()
            and os.path.normpath(source) not in generated
        ):
            missing.add(source)
        if node.tag != "generate":
            continue
        name, export_uri, target = node.get("name"), node.get("exportUri"), node.get("target", "")
        if name and export_uri and re.search(r"(?:^|[,\s])XLSX(?:$|[,\s(])", target, re.IGNORECASE):
            generated.add(os.path.normpath(str(Path("output") / export_uri / f"{name}.xlsx")))
    return [f"missing XLSX source {source}; no same-descriptor producer" for source in missing]


def dynamic_count_evidence(path: Path, root: ET.Element) -> list[str]:
    dynamic_names = {
        node.get("name")
        for node in root.iter("generate")
        if node.get("name") is not None
        and (node.get("count") is None or not node.get("count", "").isdigit())
    }
    if not dynamic_names:
        return []
    evidence: list[str] = []
    for source in sorted(path.parent.glob("*.py")):
        lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
        for start, line in enumerate(lines):
            if not re.match(r"\s*def test_", line) or path.name not in "\n".join(lines[start:]):
                continue
            end = next(
                (index for index in range(start + 1, len(lines)) if re.match(r"\s*def test_", lines[index])),
                len(lines),
            )
            body = "\n".join(lines[start:end])
            if path.name not in body:
                continue
            assertions = [
                f"{source.relative_to(REPO)}:{index + 1}"
                for index in range(start, end)
                if "assert " in lines[index]
            ]
            if assertions:
                evidence.append(
                    f"{source.relative_to(REPO)}:{start + 1} tests {', '.join(sorted(dynamic_names))}; "
                    f"assertions at {', '.join(assertions)}"
                )
    return evidence


def inventory() -> list[dict[str, Any]]:
    tracked = subprocess.run(
        [
            "git",
            "ls-files",
            "--",
            "datamimic_ce/demos/**/*.xml",
            "datamimic_ce/resources/demos/**/*.xml",
            "tests_ce/**/*.xml",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    paths = [REPO / path for path in tracked]
    records: list[dict[str, Any]] = []
    for path in paths:
        relative = path.relative_to(REPO).as_posix()
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as error:
            categories = ["non-descriptor"]
            evidence = [f"XML parse error: {error}"]
            if relative.startswith("tests_ce/unit_tests/test_authoring/fixtures/"):
                categories.append("authoring-fixture")
                evidence.append("unit_tests/test_authoring/fixtures path; malformed parser fixture")
            if "external_service_tests" in path.parts:
                categories.append("external-service")
                evidence.append("tests_ce/external_service_tests suite")
            records.append({"path": relative, "category": categories, "evidence": evidence})
            continue
        if root.tag != "setup":
            categories = ["non-descriptor"]
            evidence = [f"XML root is <{root.tag}>"]
            if "external_service_tests" in path.parts:
                categories.append("external-service")
                evidence.append("tests_ce/external_service_tests suite")
            records.append({"path": relative, "category": categories, "evidence": evidence})
            continue
        tags = sorted({node.tag.rsplit("}", 1)[-1].lower() for node in root.iter()})
        database_nodes = [
            node for node in root.iter() if node.tag.rsplit("}", 1)[-1].lower() == "database"
        ]
        sqlite_only_databases = bool(database_nodes) and all(
            node.get("dbms") == "sqlite" for node in database_nodes
        )
        categories: list[str] = []
        evidence: list[str] = []
        if relative.startswith("tests_ce/unit_tests/test_authoring/fixtures/"):
            categories.append("authoring-fixture")
            evidence.append("unit_tests/test_authoring/fixtures path; fixture consumed by authoring tests")
        external_clients = {"mongodb", "kafka", "object-storage"} & set(tags)
        if (
            "external_service_tests" in path.parts
            or external_clients
            or ("database" in tags and not sqlite_only_databases)
        ):
            categories.append("external-service")
            source = (
                "tests_ce/external_service_tests suite"
                if "external_service_tests" in path.parts
                else "descriptor client element"
            )
            clients = (
                ",".join(sorted(tag for tag in tags if tag in {"database", "mongodb", "kafka", "object-storage"}))
                or "suite policy"
            )
            evidence.append(f"{source}; client tags={clients}")
        expected_error = test_evidence(path)
        counts = {
            name: {
                "mode": "static" if value is not None and value.isdigit() else "dynamic",
                "expression": value,
            }
            for name, value in descriptor_generate_counts(path).items()
        }
        dynamic_evidence = dynamic_count_evidence(path, root)
        if counts and any(item["mode"] == "dynamic" for item in counts.values()):
            evidence.extend(dynamic_evidence)
        if expected_error:
            categories.append("intentionally-invalid")
            evidence.append(expected_error)
        fixture_evidence = missing_xlsx_source_evidence(path, root)
        if fixture_evidence:
            categories.append("missing-xlsx-source")
            evidence.extend(fixture_evidence)
        if not categories:
            categories.append("runnable")
            evidence.append("well-formed <setup>; no external service client or explicit expected-error test")
        records.append(
            {
                "path": relative,
                "category": categories,
                "evidence": evidence,
                "seeded": "rngSeed" in root.attrib,
                "generate_counts": counts,
            }
        )
    return records


def run_descriptor(record: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    relative = record["path"]
    path = REPO / relative
    categories = record["category"]
    if "non-descriptor" in categories and "authoring-fixture" not in categories:
        return relative, {"status": "NOT-A-DESCRIPTOR", "category": categories, "evidence": record["evidence"]}
    if "missing-xlsx-source" in categories:
        return relative, {
            "status": "UNVERIFIED",
            "category": categories,
            "reason": "UNVERIFIED: referenced XLSX source is absent and not generated by this descriptor",
            "evidence": record["evidence"],
        }
    if "external-service" in categories or "authoring-fixture" in categories:
        reason = (
            "UNVERIFIED: service inventory unavailable; Podman could not connect, and no other service was evidenced"
            if "external-service" in categories
            else "UNVERIFIED: authoring fixture is not a standalone runtime descriptor"
        )
        return relative, {
            "status": "UNVERIFIED",
            "category": categories,
            "reason": reason,
            "evidence": record["evidence"],
        }
    with tempfile.TemporaryDirectory(prefix="dm-step0-") as temp:
        staged = Path(temp) / path.parent.name
        shutil.copytree(path.parent, staged, ignore=shutil.ignore_patterns("output", "__pycache__", ".pytest_cache"))
        staged_descriptor = staged / path.name
        env = {**os.environ, "PYTHONPATH": str(REPO), "RUNTIME_ENVIRONMENT": "development"}
        try:
            completed = subprocess.run(
                [sys.executable, "-c", CHILD, str(staged_descriptor)],
                cwd=staged,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return relative, {
                "status": "UNRUNNABLE",
                "outcome": "timeout",
                "category": categories,
                "seconds": TIMEOUT_SECONDS,
            }
        marker = next(
            (line[len(RESULT_PREFIX) :] for line in completed.stdout.splitlines() if line.startswith(RESULT_PREFIX)),
            None,
        )
        if marker is None:
            return relative, {
                "status": "UNRUNNABLE",
                "outcome": f"no-result(exit {completed.returncode})",
                "category": categories,
                "stderr": completed.stderr[-3000:],
            }
        result = json.loads(marker)
        if completed.returncode != 0:
            return relative, {
                "status": "UNRUNNABLE",
                "category": categories,
                "process_exit": completed.returncode,
                "result": result,
                "stderr": completed.stderr[-3000:],
            }
        expected_error = "intentionally-invalid" in categories
        status = (
            "EXPECTED-ERROR"
            if expected_error and result["outcome"] != "ok"
            else "UNEXPECTED-SUCCESS"
            if expected_error
            else "UNRUNNABLE"
            if result["outcome"] != "ok"
            else "CAPTURED"
        )
        if status == "CAPTURED" and not result.get("seeded"):
            output_files = result.get("output_files") or []
            output_schemas = result.get("output_schemas")
            if not isinstance(output_schemas, dict) or set(output_schemas) != set(output_files):
                missing = sorted(set(output_files) ^ set(output_schemas or {}))
                status = "UNVERIFIED"
                detail = ", ".join(missing) or "incomplete schema evidence"
                result["reason"] = "UNVERIFIED: output schema capture unavailable for " + detail
            expected_formats = result.get("output_schema_expected_formats") or []
            missing_formats = [
                suffix for suffix in expected_formats
                if not any(path.endswith("." + suffix) for path in output_files)
            ]
            if result.get("output_schema_expected") and not output_files:
                status = "UNVERIFIED"
                result["reason"] = "UNVERIFIED: output schema unavailable for declared JSON/XML output"
            elif missing_formats:
                status = "UNVERIFIED"
                result["reason"] = (
                    "UNVERIFIED: output schema unavailable for declared "
                    + ", ".join(missing_formats)
                    + " output"
                )
            if status == "CAPTURED":
                contracts, uncertain_products, unvisited_list, unknown_scope = nested_list_count_contract(path)
                products = result.get("products")
                if unvisited_list or uncertain_products:
                    affected = ", ".join(sorted(uncertain_products)) or "nestedKey list"
                    status = "UNVERIFIED"
                    result["reason"] = f"UNVERIFIED: nested list cardinality is dynamic or ambiguous for {affected}"
                elif not isinstance(products, dict):
                    status = "UNVERIFIED"
                    result["reason"] = "UNVERIFIED: nested list cardinality evidence is missing"
                else:
                    missing_products = sorted(
                        name for name, expected in contracts.items() if expected and name not in products
                    )
                    if missing_products:
                        status = "UNVERIFIED"
                        result["reason"] = (
                            "UNVERIFIED: nested list cardinality evidence is missing for "
                            + ", ".join(missing_products)
                        )
                    for name, product in products.items():
                        if status != "CAPTURED":
                            break
                        expected = contracts.get(name, {})
                        observed = product.get("nested_cardinalities") if isinstance(product, dict) else None
                        root_count = product.get("rows") if isinstance(product, dict) else None
                        if not matches_nested_cardinalities(observed, expected, root_count):
                            status = "UNVERIFIED"
                            result["reason"] = (
                                "UNVERIFIED: nested list cardinality evidence is missing or mismatched "
                                f"for {name}"
                            )
                            break
                        product["nested_cardinality_contract"] = expected
                    if status == "CAPTURED":
                        expected_outputs = list(contracts.values()) or [{}]
                        has_nested_arrays = any(
                            bool(product.get("nested_cardinalities"))
                            for product in products.values()
                            if isinstance(product, dict)
                        ) or any(
                            bool(schema.get("nested_cardinalities"))
                            for schema in (result.get("output_schemas") or {}).values()
                            if isinstance(schema, dict)
                        )
                        if unknown_scope and has_nested_arrays:
                            status = "UNVERIFIED"
                            result["reason"] = (
                                "UNVERIFIED: nested list cardinality scope includes a nested "
                                "generate or include"
                            )
                        for output_path, schema in (result.get("output_schemas") or {}).items():
                            if status != "CAPTURED":
                                break
                            if not output_path.endswith(".json"):
                                continue
                            observed = schema.get("nested_cardinalities") if isinstance(schema, dict) else None
                            output_count = schema.get("length") if isinstance(schema, dict) else None
                            output_contract = next(
                                (
                                    expected
                                    for expected in expected_outputs
                                    if matches_nested_cardinalities(observed, expected, output_count)
                                ),
                                None,
                            )
                            if output_contract is None:
                                status = "UNVERIFIED"
                                result["reason"] = (
                                    "UNVERIFIED: JSON output nested list cardinality evidence is "
                                    f"missing or ambiguous for {output_path}"
                                )
                                break
                            schema["nested_cardinality_contract"] = output_contract
        result.update({"status": status, "category": categories, "evidence": record["evidence"]})
        result["generate_counts"] = record.get("generate_counts", {})
        return relative, result


def projections() -> dict[str, Any]:
    env = {**os.environ, "PYTHONPATH": str(REPO)}
    cli_module = (
        "datamimic_ce.interfaces.cli"
        if (REPO / "datamimic_ce/interfaces/cli.py").is_file()
        or (REPO / "datamimic_ce/interfaces/cli/__main__.py").is_file()
        else "datamimic_ce.cli"
    )
    commands = {
        "capabilities": [sys.executable, "-m", cli_module, "capabilities", "--full"],
        "reference_authoring": [sys.executable, "-m", cli_module, "reference", "authoring"],
        "reference_scaffold": [sys.executable, "-m", cli_module, "reference", "scaffold"],
    }
    captured: dict[str, Any] = {}
    for name, command in commands.items():
        result = subprocess.run(command, cwd=REPO, env=env, capture_output=True, check=True)
        captured[name] = {
            "sha256": sha256(result.stdout),
            "bytes": len(result.stdout),
            "content": result.stdout.decode("utf-8"),
        }
    from datamimic_ce.authoring.application.compiler import compile_authoring_spec
    from datamimic_ce.authoring.spec import AuthoringSpecV1

    spec = AuthoringSpecV1.model_validate(
        {
            "version": "1",
            "seed": 7,
            "products": [
                {
                    "kind": "generated",
                    "name": "step0",
                    "count": 2,
                    "fields": [
                        {"kind": "increment", "name": "id"},
                        {"kind": "values", "name": "region", "values": ["north", "south"]},
                    ],
                }
            ],
        }
    )
    xml = compile_authoring_spec(spec).xml
    captured["compiler"] = {"sha256": sha256(xml.encode("utf-8")), "bytes": len(xml.encode("utf-8")), "content": xml}
    return captured


def self_test() -> None:
    assert sha256(b"datamimic") == "be67f5f75a8fc1039d72c469d48a585c6f9f6a31391b7cd476b08c4099bba74f"
    assert test_evidence(REPO / "tests_ce/integration_tests/test_timeseries/invalid_partial_window.xml") is not None
    assert test_evidence(REPO / "tests_ce/integration_tests/test_timeseries/basic_one_series.xml") is None
    assert test_evidence(REPO / "tests_ce/functional_tests/test_condition/test_condition.xml") is None
    with tempfile.TemporaryDirectory(prefix="dm-oracle-self-test-", dir=REPO) as temp:
        descriptor = Path(temp) / "descriptor.xml"
        descriptor.write_text('<setup><generate source="fixture.xlsx"/></setup>', encoding="utf-8")
        assert missing_xlsx_source_evidence(descriptor, ET.parse(descriptor).getroot())

        descriptor.write_text(
            '<setup><generate name="src_rows" exportUri="source_out" '
            'target="CSV,JSON,XML,XLSX,DbUnit,FixedWidth(columns=\'id[4],name[16]\')"/>'
            '<generate source="output/source_out/src_rows.xlsx"/></setup>',
            encoding="utf-8",
        )
        assert not missing_xlsx_source_evidence(descriptor, ET.parse(descriptor).getroot())

        descriptor.write_text(
            '<setup><generate source="output/source_out/src_rows.xlsx"/>'
            '<generate name="src_rows" exportUri="source_out" target="XLSX"/></setup>',
            encoding="utf-8",
        )
        assert missing_xlsx_source_evidence(descriptor, ET.parse(descriptor).getroot())

        descriptor.write_text(
            '<setup><generate name="src_rows" exportUri="source_out" target="XLSXEncoder"/>'
            '<generate source="output/source_out/src_rows.xlsx"/></setup>',
            encoding="utf-8",
        )
        assert missing_xlsx_source_evidence(descriptor, ET.parse(descriptor).getroot())

        (Path(temp) / "fixture.xlsx").touch()
        descriptor.write_text('<setup><generate source="fixture.xlsx"/></setup>', encoding="utf-8")
        assert not missing_xlsx_source_evidence(descriptor, ET.parse(descriptor).getroot())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("out", nargs="?")
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--limit", type=int, help="Run only the first N local cases for a smoke check")
    parser.add_argument("--only", nargs="*", help="Run named descriptor paths while retaining the full inventory")
    parser.add_argument(
        "--capture-only", action="store_true", help="Record raw projection drift for later snapshot comparison"
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("Step-0 oracle self-test passed")
        return
    if not args.out:
        parser.error("out path required")
    cases = inventory()
    selected = [item for item in cases if item["path"] in set(args.only)] if args.only is not None else cases
    if args.limit is not None:
        selected = selected[: args.limit]
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        results = dict(pool.map(run_descriptor, selected))
    captured_projections = projections()
    projection_hashes = {name: value["sha256"] for name, value in captured_projections.items()}
    expected = {"capabilities": CAPABILITIES_SHA256, "reference_authoring": AUTHORING_REFERENCE_SHA256}
    drift = {
        name: {"expected": expected[name], "actual": projection_hashes[name]}
        for name in expected
        if projection_hashes[name] != expected[name]
    }
    counts: dict[str, int] = {}
    for item in cases:
        categories = item["category"] if isinstance(item["category"], list) else [item["category"]]
        for category in categories:
            counts[category] = counts.get(category, 0) + 1
    statuses: dict[str, int] = {}
    for result in results.values():
        status = result["status"]
        statuses[status] = statuses.get(status, 0) + 1
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.strip()
    output = {
        "commit": commit,
        "inventory_count": len(cases),
        "category_counts_overlapping": counts,
        "statuses": statuses,
        "inventory": cases,
        "descriptors": results,
        "projections": captured_projections,
        "projection_drift": drift,
    }
    Path(args.out).write_text(json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"{len(cases)} XML files inventoried; {len(selected)} selected; "
        f"status counts: {json.dumps(statuses, sort_keys=True)}"
    )
    print(f"projection hashes: {json.dumps(projection_hashes, sort_keys=True)}")
    if drift:
        print(f"projection drift: {json.dumps(drift, sort_keys=True)}")
        if not args.capture_only:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
