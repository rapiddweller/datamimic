# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""One-time, non-executing migration from the frozen CE intent compiler."""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, TypeAdapter, ValidationError

from datamimic_ce.authoring.domain.common import NonEmptyStrictStr
from datamimic_ce.authoring.domain.expectations import ExpectationIntent
from datamimic_ce.authoring.domain.proof import FieldRole, ProductRoleDeclaration
from datamimic_ce.authoring.domain.requests import (
    BuildRequestV4,
    DecompileDocumentRequest,
    HexSha256,
    RejectedDecompileDocument,
)

LEGACY_REVISION = "84a9f4657148bcfa0bc560908ed42b1d5fa3efab"
_JSON_OBJECT = TypeAdapter(dict[str, JsonValue])
_EXPECTATION: TypeAdapter[ExpectationIntent] = TypeAdapter(ExpectationIntent)


class MigrationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LegacyField(MigrationModel):
    name: NonEmptyStrictStr
    list_field: NonEmptyStrictStr | None = None
    roles: list[FieldRole] = Field(default_factory=list)


class LegacyProduct(MigrationModel):
    name: NonEmptyStrictStr
    fields: list[LegacyField]


class LegacyRelationship(MigrationModel):
    kind: Literal["nested", "memstore_source"]
    parent: NonEmptyStrictStr
    child: NonEmptyStrictStr
    source_id: NonEmptyStrictStr | None = None


class LegacyUnresolved(MigrationModel):
    product: NonEmptyStrictStr
    aspect: NonEmptyStrictStr
    reason: NonEmptyStrictStr


class LegacyPlan(MigrationModel):
    products: list[LegacyProduct]
    derived_acceptance: list[dict[str, JsonValue]]
    relationships: list[LegacyRelationship]
    unresolved: list[LegacyUnresolved]


class LegacyPayload(MigrationModel):
    expectations: list[dict[str, JsonValue]]
    acceptance_requirements: list[dict[str, JsonValue]] = Field(default_factory=list)
    plan: LegacyPlan


def _location(parts: tuple[str | int, ...]) -> str:
    return "".join(
        f"[{part}]" if isinstance(part, int) else (f".{part}" if index else part) for index, part in enumerate(parts)
    )


def _validation_path(error: ValidationError, prefix: str = "") -> ValueError:
    location = _location(error.errors(include_input=False)[0]["loc"])
    return ValueError(f"{prefix}{'.' if prefix and location else ''}{location}: invalid or unsupported migration data")


def _expectation(item: dict[str, JsonValue], path: str, *, derived: bool = False) -> dict[str, JsonValue]:
    data = item.copy()
    kind = data.get("kind")
    allowed = {
        "exact_count": {"kind", "product", "list_field", "exact_count" if derived else "count"},
        "per_parent_count": {
            "kind",
            "parent_product",
            "product" if derived else "child_product",
            "count_per_parent" if derived else "count",
        },
        "unique": {"kind", "product", "list_field", "field", "scope"},
        "foreign_key": {
            "kind",
            "product" if derived else "child_product",
            "child_field",
            "parent_product",
            "parent_field",
        },
        "allowed_values": {"kind", "product", "list_field", "field", "allowed_values" if derived else "values"},
        "range": {"kind", "product", "list_field", "field", "minimum", "maximum"},
        "row_condition": {"kind", "product", "condition", "result_type"},
    }
    if not isinstance(kind, str) or kind not in allowed:
        raise ValueError(f"{path}.kind: unsupported legacy expectation")
    unknown = sorted(data.keys() - allowed[kind])
    if unknown:
        raise ValueError(f"{path}.{unknown[0]}: unsupported legacy field")
    if kind == "foreign_key":
        child_product = data.pop("product" if derived else "child_product", None)
        child_field = data.pop("child_field", None)
        parent_product = data.pop("parent_product", None)
        parent_field = data.pop("parent_field", None)
        data["child"] = {"subject": {"kind": "product", "product": child_product}, "field": child_field}
        data["parent"] = {"subject": {"kind": "product", "product": parent_product}, "field": parent_field}
    elif kind == "per_parent_count":
        child_product = data.pop("product" if derived else "child_product", None)
        parent_product = data.pop("parent_product", None)
        data["subject"] = {"kind": "per_parent", "parent_product": parent_product, "child_product": child_product}
        if derived:
            data["count"] = data.pop("count_per_parent", None)
    elif kind in {"exact_count", "unique", "allowed_values", "range", "row_condition"}:
        subject: dict[str, JsonValue] = {"kind": "product", "product": data.pop("product", None)}
        list_field = data.pop("list_field", None)
        if list_field is not None:
            subject["list_field"] = list_field
        data["subject"] = subject
        if derived and kind == "exact_count":
            data["count"] = data.pop("exact_count", None)
        if derived and kind == "allowed_values":
            data["values"] = data.pop("allowed_values", None)
    else:
        raise ValueError(f"{path}.kind: unsupported legacy expectation")
    try:
        # JSON-mode validation retains strict integer checks while accepting JSON arrays.
        result = _EXPECTATION.validate_json(json.dumps(data))
    except ValidationError as error:
        raise _validation_path(error, path) from error
    return _JSON_OBJECT.validate_python(result.model_dump(mode="json", exclude_none=True, exclude_unset=True))


def transaction_from_legacy(payload: object) -> dict[str, JsonValue]:
    """Transfer every proof declaration; syntax alone cannot recover field roles."""
    try:
        legacy = LegacyPayload.model_validate(payload)
    except ValidationError as error:
        raise _validation_path(error) from error
    expectations: list[JsonValue] = [
        _expectation(item, f"expectations[{index}]") for index, item in enumerate(legacy.expectations)
    ]
    requirements: list[JsonValue] = [
        {"origin": "derived", "expectation": _expectation(item, f"plan.derived_acceptance[{index}]", derived=True)}
        for index, item in enumerate(legacy.plan.derived_acceptance)
    ]
    requirements.extend(
        {"origin": "caller", "expectation": _expectation(item, f"acceptance_requirements[{index}]")}
        for index, item in enumerate(legacy.acceptance_requirements)
    )
    roles: list[JsonValue] = []
    for product in legacy.plan.products:
        for field in product.fields:
            for role in field.roles:
                declaration = ProductRoleDeclaration(
                    product=product.name, field=field.name, list_field=field.list_field, role=role
                )
                roles.append(_JSON_OBJECT.validate_python(declaration.model_dump(mode="json", exclude_none=True)))
    return {"expectations": expectations, "acceptance_requirements": requirements, "product_roles": roles}


# Only the selected, verified old source is imported in this isolated interpreter.
_LEGACY_PROGRAM = r"""
import json, pathlib, subprocess, sys
source = pathlib.Path(sys.argv[1]).resolve()
def git(*args):
    return subprocess.run(["git", "-C", str(source), *args], capture_output=True, text=True, check=True).stdout.strip()
try:
    if git("rev-parse", "HEAD") != sys.argv[2]:
        raise ValueError("legacy_source: frozen CE revision required")
    if git("status", "--porcelain", "--untracked-files=all", "--", "datamimic_ce"):
        raise ValueError("legacy_source: package source must be clean")
    tracked = set(git("ls-files", "--", "datamimic_ce").splitlines())
    if any(str(path.relative_to(source)) not in tracked for path in (source / "datamimic_ce").rglob("*.py")):
        raise ValueError("legacy_source: untracked Python source is forbidden")
except (OSError, subprocess.CalledProcessError):
    print(json.dumps({"error": "legacy_source: cannot verify frozen CE source"}))
    sys.exit(1)
except ValueError as error:
    print(json.dumps({"error": str(error)}))
    sys.exit(1)
sys.path.insert(0, str(source))
from pydantic import ValidationError
from datamimic_ce.authoring import spec as spec_module
from datamimic_ce.authoring.application import compiler
from datamimic_ce.authoring.application.intent_validation import project_validation_issues
from datamimic_ce.authoring.contracts import AuthoringExpectation
from datamimic_ce.authoring.domain.derived_facts import derive_facts
if (pathlib.Path(spec_module.__file__).resolve() != source / "datamimic_ce/authoring/spec.py"
    or pathlib.Path(compiler.__file__).resolve() != source / "datamimic_ce/authoring/application/compiler.py"):
    print(json.dumps({"error": "legacy_source: compiler origin mismatch"}))
    sys.exit(1)
def reject(path):
    print(json.dumps({"error": f"{path}: invalid legacy input"}))
    sys.exit(1)
def location(parts):
    return "".join(f"[{p}]" if isinstance(p, int) else (f".{p}" if i else p) for i, p in enumerate(parts))
request = json.load(sys.stdin)
try:
    spec = spec_module.AuthoringSpecV1.model_validate(request["spec"])
except ValidationError as error:
    parts = project_validation_issues(error, request["spec"])[0].path if isinstance(request["spec"], dict) else ()
    reject("spec" + ("." + location(parts) if parts else ""))
if not isinstance(request["acceptance_requirements"], list):
    reject("acceptance_requirements")
caller = []
for index, value in enumerate(request["acceptance_requirements"]):
    try:
        caller.append(AuthoringExpectation.model_validate(value))
    except ValidationError as error:
        parts = error.errors(include_input=False)[0]["loc"]
        if isinstance(value, dict) and parts and parts[0] == value.get("kind"):
            parts = parts[1:]
        reject(f"acceptance_requirements[{index}]" + ("." + location(parts) if parts else ""))
try:
    compiled = compiler.compile_authoring_spec(spec)
except compiler.CompileError:
    print(json.dumps({"error": "spec: frozen compiler rejected legacy input"}))
    sys.exit(1)
products = []
def collect(product):
    fields = []
    for field in product.fields:
        fields.append({"name": field.name, "roles": [role.model_dump(mode="json") for role in field.roles]})
        if isinstance(field, spec_module.NestedListField):
            for inner in field.fields:
                fields.append({"name": inner.name, "list_field": field.name,
                               "roles": [role.model_dump(mode="json") for role in inner.roles]})
    products.append({"name": product.name, "fields": fields})
    if isinstance(product, spec_module.GeneratedProduct):
        for child in product.children:
            collect(child)
for product in spec.products:
    collect(product)
plan = compiled.plan.model_dump(mode="json")
print(json.dumps({"xml": compiled.xml,
                  "expectations": [item.model_dump(mode="json") for item in spec.expectations],
                  "acceptance_requirements": [item.model_dump(mode="json") for item in caller],
                  "plan": {**plan, "products": products}, "legacy_plan": plan,
                  "legacy_facts": derive_facts(compiled.plan).model_dump(mode="json")}))
"""


class LegacyCompilerResult(LegacyPayload):
    xml: NonEmptyStrictStr
    legacy_plan: dict[str, JsonValue]
    legacy_facts: dict[str, JsonValue]


class MigrationReceipt(MigrationModel):
    kind: Literal["legacy_authoring_migration"] = "legacy_authoring_migration"
    legacy_revision: NonEmptyStrictStr = LEGACY_REVISION
    input_sha256: HexSha256
    legacy_xml_sha256: HexSha256
    xml_filename: NonEmptyStrictStr
    legacy_plan: dict[str, JsonValue]
    legacy_facts: dict[str, JsonValue]
    build_request: BuildRequestV4


def migrate(
    input_path: Path,
    *,
    legacy_source: Path,
    legacy_python: Path,
    xml_output: Path,
    acceptance_requirements: Path | None = None,
    smoke_export: bool = False,
    deterministic_replay: bool = False,
    max_count: int = 10,
    sample_rows: int = 5,
) -> MigrationReceipt:
    """Compile without execution; exclusive XML creation preserves project resources."""
    original = input_path.resolve(strict=True)
    output = xml_output.absolute()
    if output.parent.resolve(strict=True) != original.parent or output.suffix.lower() != ".xml":
        raise ValueError("xml_output: choose a new XML filename beside the original input")
    if output.exists() or output.is_symlink():
        raise ValueError("xml_output: overwrite is forbidden")
    original_bytes = original.read_bytes()
    request = {
        "spec": json.loads(original_bytes),
        "acceptance_requirements": (
            json.loads(acceptance_requirements.read_bytes()) if acceptance_requirements is not None else []
        ),
    }
    process = subprocess.run(
        [str(legacy_python), "-I", "-B", "-c", _LEGACY_PROGRAM, str(legacy_source), LEGACY_REVISION],
        input=json.dumps(request),
        text=True,
        capture_output=True,
        cwd=original.parent,
        timeout=60,
    )
    if process.returncode:
        try:
            failure = _JSON_OBJECT.validate_json(process.stdout)
        except ValidationError:
            raise ValueError("legacy_source: isolated compiler failed") from None
        message = failure.get("error")
        if isinstance(message, str):
            raise ValueError(message)
        raise ValueError("legacy_source: isolated compiler failed")
    try:
        legacy = LegacyCompilerResult.model_validate_json(process.stdout)
    except ValidationError as error:
        raise _validation_path(error, "legacy_result") from error
    transaction = transaction_from_legacy(legacy.model_dump(exclude={"xml", "legacy_plan", "legacy_facts"}))
    from datamimic_ce.authoring import create_authoring_application

    logical_path = PurePosixPath(output.name)
    application = create_authoring_application(workspace_root=original.parent, descriptor_path=logical_path)
    decompiled = application.decompile_document(DecompileDocumentRequest(xml=legacy.xml, descriptor_path=logical_path))
    if isinstance(decompiled, RejectedDecompileDocument):
        path = _location(decompiled.diagnostics[0].path)
        raise ValueError(f"xml{'.' if path else ''}{path}: unsupported migrated XML")
    document = decompiled.document
    build = BuildRequestV4.model_validate(
        {
            "document": document,
            **transaction,
            "descriptor_path": output.name,
            "verification": {"smoke_export": smoke_export, "deterministic_replay": deterministic_replay},
            "max_count": max_count,
            "sample_rows": sample_rows,
        }
    )
    receipt = MigrationReceipt(
        input_sha256=hashlib.sha256(original_bytes).hexdigest(),
        legacy_xml_sha256=hashlib.sha256(legacy.xml.encode()).hexdigest(),
        xml_filename=output.name,
        legacy_plan=legacy.legacy_plan,
        legacy_facts=legacy.legacy_facts,
        build_request=build,
    )
    with output.open("x", encoding="utf-8", newline="") as stream:
        stream.write(legacy.xml)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--legacy-source", type=Path, required=True)
    parser.add_argument("--legacy-python", type=Path, required=True)
    parser.add_argument("--xml-output", type=Path, required=True)
    parser.add_argument("--acceptance-requirements", type=Path)
    parser.add_argument("--smoke-export", action="store_true")
    parser.add_argument("--deterministic-replay", action="store_true")
    parser.add_argument("--max-count", type=int, default=10)
    parser.add_argument("--sample-rows", type=int, default=5)
    args = parser.parse_args()
    try:
        receipt = migrate(
            args.input,
            legacy_source=args.legacy_source,
            legacy_python=args.legacy_python,
            xml_output=args.xml_output,
            acceptance_requirements=args.acceptance_requirements,
            smoke_export=args.smoke_export,
            deterministic_replay=args.deterministic_replay,
            max_count=args.max_count,
            sample_rows=args.sample_rows,
        )
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, ValidationError):
        print(json.dumps({"error": "migration: invalid input or inaccessible migration resource"}))
        return 1
    except ValueError as error:
        print(json.dumps({"error": str(error)}))
        return 1
    print(receipt.model_dump_json(exclude_none=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
