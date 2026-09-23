"""Capture descriptor behavior and canonical authoring projections at Step 0.

Run with the project interpreter:
    .venv/bin/python script/architecture_study/verify_step0.py /tmp/step0.json
"""

from __future__ import annotations

import argparse
import ast
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
from datamimic_ce.data_mimic_test import DataMimicTest

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
        return {"type": "object", "fields": {key: shape(value) for key, value in sorted(item.items())}}
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
    non_null = [value for value in items if value is not None]
    if non_null:
        items = non_null
    if items and all(isinstance(value, list) for value in items):
        members = [member for value in items for member in value]
        return {"type": "array", "items": shape_union(members) if members else "unknown"}
    if items and all(isinstance(value, dict) for value in items):
        members = [member for value in items for member in value.values()]
        return {"type": "object", "values": shape_union(members) if members else "unknown"}
    members = sorted({json.dumps(shape(value), sort_keys=True) for value in items})
    if len(members) == 1:
        return json.loads(members[0])
    return {"type": "union", "values": [json.loads(value) for value in members]}

def shape_rows(rows):
    if not isinstance(rows, list) or not rows:
        return shape(rows)
    if all(isinstance(row, dict) for row in rows):
        keys = sorted({key for row in rows for key in row})
        return {
            "type": "object",
            "fields": {
                key: shape_union([row[key] for row in rows if key in row])
                for key in keys
            },
        }
    return shape_union(rows)

def generate_counts(path):
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return {}
    return {
        node.get("name"): node.get("count")
        for node in root.iter("generate")
        if node.get("name") is not None
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
counts = generate_counts(path)
try:
    seeded = "rngSeed" in ET.parse(path).getroot().attrib
    engine = DataMimicTest(test_dir=path.parent, filename=path.name, capture_test_result=True)
    task_id = engine.task_id
    engine.test_with_timer()
    result = engine.capture_result()
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
                    "rows": (
                        (len(rows) if isinstance(rows, list) else 1)
                        if name in counts and counts[name] is not None and counts[name].isdigit()
                        else "dynamic"
                    ),
                    "value_shape": shape_rows(rows),
                }
                for name, rows in sorted(products.items())
            },
        }
    output = path.parent / "output"
    files = {}
    if output.is_dir():
        for item in sorted(output.rglob("*")):
            if item.is_file():
                relative = item.relative_to(output)
                if task_id is not None and relative.parts[0] == task_id:
                    relative = Path(*relative.parts[1:])
                files[str(relative)] = output_digest(item)
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
except Exception as error:
    record = {
        "outcome": type(error).__name__, "seeded": seeded,
        "message": str(error).replace(str(path.parent), "<descriptor-dir>"),
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


def test_fixture_evidence(path: Path, root: ET.Element) -> list[str]:
    missing = sorted(
        {
            source
            for node in root.iter()
            if (source := node.get("source"))
            and Path(source).suffix.lower() == ".xlsx"
            and not (path.parent / source).is_file()
        }
    )
    evidence: list[str] = []
    for filename in missing:
        for source in sorted(path.parent.glob("*.py")):
            try:
                tree = ast.parse(source.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError:
                continue
            workbook_creation = any(isinstance(node, ast.Name) and node.id == "Workbook" for node in ast.walk(tree))
            dir_proven = False
            for statement in tree.body:
                if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                binds_dir = any(
                    isinstance(node, ast.Name) and node.id == "_DIR" and isinstance(node.ctx, (ast.Store, ast.Del))
                    for node in ast.walk(statement)
                )
                if not binds_dir:
                    continue
                value = statement.value if isinstance(statement, ast.Assign) else None
                dir_proven = (
                    isinstance(statement, ast.Assign)
                    and len(statement.targets) == 1
                    and isinstance(statement.targets[0], ast.Name)
                    and statement.targets[0].id == "_DIR"
                    and isinstance(value, ast.Attribute)
                    and value.attr == "parent"
                    and isinstance(value.value, ast.Call)
                    and isinstance(value.value.func, ast.Attribute)
                    and value.value.func.attr == "resolve"
                    and isinstance(value.value.func.value, ast.Call)
                    and isinstance(value.value.func.value.func, ast.Name)
                    and value.value.func.value.func.id == "Path"
                    and value.value.func.value.args
                    and isinstance(value.value.func.value.args[0], ast.Name)
                    and value.value.func.value.args[0].id == "__file__"
                )
            matches: list[tuple[int, int]] = []

            def inspect_scope(
                statements: list[ast.stmt],
                expected_filename: str,
                evidence_matches: list[tuple[int, int]],
                descriptor_dir: bool,
                module_scope: bool = False,
            ) -> None:
                assigned_paths: dict[str, int | None] = {}
                local_dir_binding = not module_scope and any(
                    isinstance(node, ast.Name)
                    and node.id == "_DIR"
                    and isinstance(node.ctx, (ast.Store, ast.Del))
                    for statement in statements
                    if not isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
                    for node in ast.walk(statement)
                )
                for statement in statements:
                    if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        inspect_scope(statement.body, expected_filename, evidence_matches, descriptor_dir)
                        continue
                    if isinstance(statement, ast.Assign):
                        value = statement.value
                        has_filename = descriptor_dir and not local_dir_binding and (
                            isinstance(value, ast.BinOp)
                            and isinstance(value.op, ast.Div)
                            and isinstance(value.left, ast.Name)
                            and value.left.id == "_DIR"
                            and isinstance(value.right, ast.Constant)
                            and value.right.value == expected_filename
                        )
                        for target in statement.targets:
                            for node in ast.walk(target):
                                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                                    assigned_paths[node.id] = None
                            if isinstance(target, ast.Name):
                                assigned_paths[target.id] = statement.lineno if has_filename else None
                    elif isinstance(statement, (ast.AnnAssign, ast.AugAssign, ast.Delete)):
                        for node in ast.walk(statement):
                            if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
                                assigned_paths[node.id] = None
                    elif isinstance(
                        statement,
                        (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith, ast.Match),
                    ):
                        for node in ast.walk(statement):
                            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                                assigned_paths[node.id] = None
                        continue
                    for node in ast.walk(statement):
                        if isinstance(node, ast.NamedExpr) and isinstance(node.target, ast.Name):
                            assigned_paths[node.target.id] = None
                    call = statement.value if isinstance(statement, (ast.Expr, ast.Return)) else None
                    if (
                        not isinstance(call, ast.Call)
                        or not isinstance(call.func, ast.Attribute)
                        or call.func.attr != "save"
                    ):
                        continue
                    if not call.args:
                        continue
                    argument = call.args[0]
                    exact_filename = descriptor_dir and not local_dir_binding and (
                        isinstance(argument, ast.BinOp)
                        and isinstance(argument.op, ast.Div)
                        and isinstance(argument.left, ast.Name)
                        and argument.left.id == "_DIR"
                        and isinstance(argument.right, ast.Constant)
                        and argument.right.value == expected_filename
                    )
                    if exact_filename:
                        evidence_matches.append((call.lineno, call.lineno))
                    elif isinstance(argument, ast.Name) and assigned_paths.get(argument.id) is not None:
                        evidence_matches.append((assigned_paths[argument.id] or call.lineno, call.lineno))

            inspect_scope(tree.body, filename, matches, dir_proven, module_scope=True)
            if matches and workbook_creation:
                reference_line, save_line = matches[0]
                evidence.append(
                    f"{source.relative_to(REPO)}:{reference_line} names {filename}; "
                    f"{source.relative_to(REPO)}:{save_line} writes the test workbook"
                )
                break
    return evidence


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
        categories: list[str] = []
        evidence: list[str] = []
        if relative.startswith("tests_ce/unit_tests/test_authoring/fixtures/"):
            categories.append("authoring-fixture")
            evidence.append("unit_tests/test_authoring/fixtures path; fixture consumed by authoring tests")
        if "external_service_tests" in path.parts or {"database", "mongodb", "kafka", "object-storage"} & set(tags):
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
        fixture_evidence = test_fixture_evidence(path, root)
        if fixture_evidence:
            categories.append("test-fixture-dependent")
            evidence.extend(fixture_evidence)
        if not categories:
            categories.append("runnable")
            evidence.append("well-formed <setup>; no service client or explicit expected-error test")
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
    if "test-fixture-dependent" in categories:
        return relative, {
            "status": "UNVERIFIED",
            "category": categories,
            "reason": (
                "UNVERIFIED: source workbook is generated by sibling test setup and "
                "absent from the descriptor directory"
            ),
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
        result.update({"status": status, "category": categories, "evidence": record["evidence"]})
        result["generate_counts"] = record.get("generate_counts", {})
        return relative, result


def projections() -> dict[str, Any]:
    env = {**os.environ, "PYTHONPATH": str(REPO)}
    commands = {
        "capabilities": [sys.executable, "-m", "datamimic_ce.interfaces.cli", "capabilities", "--full"],
        "reference_authoring": [sys.executable, "-m", "datamimic_ce.interfaces.cli", "reference", "authoring"],
        "reference_scaffold": [sys.executable, "-m", "datamimic_ce.interfaces.cli", "reference", "scaffold"],
    }
    captured: dict[str, Any] = {}
    for name, command in commands.items():
        result = subprocess.run(command, cwd=REPO, env=env, capture_output=True, check=True)
        captured[name] = {
            "sha256": sha256(result.stdout),
            "bytes": len(result.stdout),
            "content": result.stdout.decode("utf-8"),
        }
    from datamimic_ce.authoring.compiler import compile_authoring_spec
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
        cases = (
            (
                "positive",
                "_DIR = Path(__file__).resolve().parent\nWorkbook().save(_DIR / 'fixture.xlsx')",
                True,
            ),
            (
                "absolute-path-save",
                "Workbook().save(Path('/tmp') / 'fixture.xlsx')",
                False,
            ),
            ("relative-path-save", "Workbook().save('fixture.xlsx')", False),
            ("unrelated-save", "Workbook().save('other.xlsx')  # fixture.xlsx", False),
            ("suffix-save", "Workbook().save('fixture.xlsx.old')", False),
            (
                "rebound-path",
                "path = 'fixture.xlsx'\npath = 'other.xlsx'\nWorkbook().save(path)",
                False,
            ),
            (
                "separate-function-path",
                "def fixture_path():\n    path = 'fixture.xlsx'\n"
                "def save_workbook(path):\n    Workbook().save(path)\n",
                False,
            ),
            (
                "conditional-save-argument",
                "Workbook().save('fixture.xlsx' if False else 'other.xlsx')",
                False,
            ),
            (
                "conditional-path-assignment",
                "path = 'fixture.xlsx' if False else 'other.xlsx'\nWorkbook().save(path)",
                False,
            ),
            (
                "branch-rebound-path",
                "path = 'fixture.xlsx'\nif True:\n    path = 'other.xlsx'\nWorkbook().save(path)",
                False,
            ),
            (
                "augmented-path-rebind",
                "path = 'fixture.xlsx'\npath += '.old'\nWorkbook().save(path)",
                False,
            ),
            (
                "annotated-path-rebind",
                "path = 'fixture.xlsx'\npath: str = 'other.xlsx'\nWorkbook().save(path)",
                False,
            ),
            (
                "deleted-path",
                "path = 'fixture.xlsx'\ndel path\nWorkbook().save(path)",
                False,
            ),
            (
                "shadowed-module-dir",
                "_DIR = Path(__file__).resolve().parent\n"
                "def save(_DIR):\n    Workbook().save(_DIR / 'fixture.xlsx')\n"
                "save(Path('/tmp'))",
                False,
            ),
            (
                "function-import-dir-alias",
                "_DIR = Path(__file__).resolve().parent\n"
                "def save():\n    from test_support import _DIR\n"
                "    Workbook().save(_DIR / 'fixture.xlsx')\nsave()",
                False,
            ),
        )
        failures: list[str] = []
        for name, body, expected in cases:
            case = Path(temp) / name
            case.mkdir()
            descriptor = case / "descriptor.xml"
            descriptor.write_text('<setup><generate source="fixture.xlsx"/></setup>', encoding="utf-8")
            (case / "test_fixture.py").write_text(
                f"from pathlib import Path\nfrom openpyxl import Workbook\n{body}\n",
                encoding="utf-8",
            )
            evidence = test_fixture_evidence(descriptor, ET.parse(descriptor).getroot())
            if bool(evidence) != expected:
                failures.append(f"{name}: expected evidence={expected}, got {evidence}")
        assert not failures, "fixture evidence cases failed:\n" + "\n".join(failures)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("out", nargs="?")
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--limit", type=int, help="Run only the first N local cases for a smoke check")
    parser.add_argument("--only", nargs="*", help="Run named descriptor paths while retaining the full inventory")
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
        raise SystemExit(1)


if __name__ == "__main__":
    main()
