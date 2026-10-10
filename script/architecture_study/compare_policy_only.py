"""Compare the audited local-only policy descriptors across two checkouts.

This is a narrow oracle: only the explicit descriptor list below can run.
Running descriptors is intentionally opt-in via ``--run`` after review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from typing import Any

from compare_step0 import equivalent
from verify_step0 import CHILD, RESULT_PREFIX

FROZEN_ROOT = Path("/private/tmp/dev-a219")
FROZEN_REVISION = "a219163e533d661bcc7bda0faa5ecc77909ab5aa"
TARGET_ROOT = Path("/private/tmp/datamimic-architecture-experiment-2")
PREFIX = "tests_ce/external_service_tests/"
ALLOWLIST = tuple(
    PREFIX + directory + "/" + name + ".xml"
    for directory, names in (
        (
            "data_source_cyclic",
            (
                "test_csv_cyclic_mp",
                "test_csv_cyclic_non_mp",
                "test_json_cyclic",
                "test_json_cyclic_non_mp",
                "test_memstore_product_cyclic",
                "test_part_cyclic_mp",
                "test_part_memstore_cyclic",
                "test_part_no_cyclic",
            ),
        ),
        (
            "integration_data_source_cyclic",
            ("test_csv_cyclic", "test_json_cyclic", "test_product_cyclic"),
        ),
    )
    for name in names
)
EXPECTED_SHA256 = {
    PREFIX + "data_source_cyclic/test_csv_cyclic_mp.xml": (
        "ded653687d85a784f966c1492a11884301fb76cf2862317c1976d515e8353ae9"
    ),
    PREFIX + "data_source_cyclic/test_csv_cyclic_non_mp.xml": (
        "5cc027823f4502d93f8906c1f3fabbe58615659c61e5cd2e143dc84772ab1044"
    ),
    PREFIX + "data_source_cyclic/test_json_cyclic.xml": (
        "77877775079d6e8091b112dd78c4b0e5e28c0c74b7f64a4ff0410823bc795c97"
    ),
    PREFIX + "data_source_cyclic/test_json_cyclic_non_mp.xml": (
        "9e15b7e1343c133fdf7d9eaf3628107241ac6bf304b5077321103ec83885f9e7"
    ),
    PREFIX + "data_source_cyclic/test_memstore_product_cyclic.xml": (
        "817afe55cf20e2f178e793fbfcea81b0d950e705d926fe3aa880b5d23fec9249"
    ),
    PREFIX + "data_source_cyclic/test_part_cyclic_mp.xml": (
        "c18c5b8ae1c51e58c74355571d4175f84b0a48fadfbbf3ab24d08f49da2a4215"
    ),
    PREFIX + "data_source_cyclic/test_part_memstore_cyclic.xml": (
        "5383322f912b0f0ffba4c66ce1ebfeb9a48d54e3fad16cb24ebecccd369400fe"
    ),
    PREFIX + "data_source_cyclic/test_part_no_cyclic.xml": (
        "6ce52570fc0c9da7c8a5b0c1c57f17af93f5d150c42f0aa63beacef76ed4f3ed"
    ),
    PREFIX + "integration_data_source_cyclic/test_csv_cyclic.xml": (
        "af8cfe8631629aa90896f5203520f4388ca36187bd1f752c04421937c2472095"
    ),
    PREFIX + "integration_data_source_cyclic/test_json_cyclic.xml": (
        "f87602602b0a27a262c43178585fb65d2bdd77a54651618b5eeddd2a0a413831"
    ),
    PREFIX + "integration_data_source_cyclic/test_product_cyclic.xml": (
        "56eed1345d37fd2cf0194e8715c32341100328bb492243843db4485ec43da2d0"
    ),
}
EXPECTED_FIXTURE_SHA256 = {
    PREFIX + "data_source_cyclic/data/products.ent.csv": (
        "6b468ff78208e5d02243bb4773b54316433b4fbbcc3c5eb004ab14c001da858f"
    ),
    PREFIX + "data_source_cyclic/data/people.json": (
        "441a6b90fd3d194ed32e2a5eb37287ad1b57fc030b7e9c10b7532a98ef44f1b9"
    ),
    PREFIX + "integration_data_source_cyclic/data/products.ent.csv": (
        "b85f095480a7f6c25bb829f6a4980e45ac36b0c0d29849f0f5830d1afa91ac18"
    ),
    PREFIX + "integration_data_source_cyclic/data/people.json": (
        "9cbd8c10f6c2e77632e86daed71912c3e67e5d3e111505c21857022f4ec925b5"
    ),
}
EXPECTED_TAGS = {"setup", "generate", "key", "nestedKey", "memstore"}
FORBIDDEN_NAMES = {"execute", "include", "script", "condition", "config", "selector"}
SERVICE_NAMES = {"database", "mongodb", "kafka", "object-storage", "objectstorage"}
LOCAL_TARGETS = {"", "consoleexporter", "mem"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def revision(root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()


def clean_package_checkout(root: Path) -> bool:
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", "datamimic_ce"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return not status.strip()


def safe_source(parent: Path, source: str) -> Path | None:
    if source == "mem":
        return None
    pure = PurePosixPath(source)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts or "\\" in source:
        raise ValueError(f"unsafe source path: {source}")
    candidate = parent.joinpath(*pure.parts)
    current = parent
    for part in pure.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symlink source path: {source}")
    if (
        not candidate.is_file()
        or not candidate.resolve().is_relative_to(parent.resolve())
    ):
        raise ValueError(f"source is not a local fixture: {source}")
    return candidate


def fixture_hashes(
    parent: Path, xml_root: ET.Element, descriptor: str, *, audit: bool = True
) -> dict[str, str]:
    sources = sorted(
        {
            node.get("source")
            for node in xml_root.iter()
            if node.get("source") and node.get("source") != "mem"
        }
    )
    hashes: dict[str, str] = {}
    for source in sources:
        path = safe_source(parent, source)
        if path is not None:
            relative = (PurePosixPath(descriptor).parent / source).as_posix()
            expected = EXPECTED_FIXTURE_SHA256.get(relative)
            actual = digest(path.read_bytes())
            if audit and (expected is None or actual != expected):
                raise ValueError(f"fixture hash is not safety-audited: {relative}")
            hashes[source] = actual
    return hashes


def validate_policy_xml(
    path: Path, relative: str, raw: bytes, *, audit_fixtures: bool = True
) -> dict[str, str]:
    xml_root = ET.fromstring(raw)
    if xml_root.tag != "setup":
        raise ValueError(f"{relative}: root must be <setup>")
    if "rngSeed" in xml_root.attrib:
        raise ValueError(f"{relative}: allowlist expects unseeded descriptors")
    memstore_ids = {node.get("id") for node in xml_root.iter("memstore")}
    for node in xml_root.iter():
        if node.tag not in EXPECTED_TAGS or node.tag.lower() in FORBIDDEN_NAMES:
            raise ValueError(f"{relative}: unsupported element <{node.tag}>")
        if node.tag.lower() in SERVICE_NAMES:
            raise ValueError(f"{relative}: service client element <{node.tag}>")
        for attribute, value in node.attrib.items():
            attribute_name = attribute.lower()
            if attribute_name in FORBIDDEN_NAMES or attribute_name in SERVICE_NAMES:
                raise ValueError(f"{relative}: forbidden attribute {attribute}")
            if value.strip().lower() in SERVICE_NAMES:
                raise ValueError(f"{relative}: service client value in {attribute}")
            if attribute_name == "source":
                if value == "mem" and value not in memstore_ids:
                    raise ValueError(f"{relative}: undeclared memstore source")
                safe_source(path.parent, value)
            if attribute_name == "target":
                targets = [item.strip().lower() for item in value.split(",")]
                if any(target not in LOCAL_TARGETS for target in targets):
                    raise ValueError(f"{relative}: non-local target {value!r}")
                if "mem" in targets and "mem" not in memstore_ids:
                    raise ValueError(f"{relative}: undeclared memstore target")
            if attribute_name in {"exporturi", "output", "filename", "filepath"}:
                raise ValueError(f"{relative}: possible file-writing attribute {attribute}")
    return fixture_hashes(path.parent, xml_root, relative, audit=audit_fixtures)


def validate_descriptor(root: Path, relative: str) -> tuple[Path, bytes, dict[str, str]]:
    if relative not in ALLOWLIST:
        raise ValueError(f"path is outside the explicit policy allowlist: {relative}")
    checkout = root.resolve()
    path = root / relative
    current = root
    for part in PurePosixPath(relative).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"descriptor path contains symlink: {relative}")
    if not path.is_file() or not path.resolve().is_relative_to(checkout):
        raise ValueError(f"descriptor missing or outside checkout: {relative}")
    raw = path.read_bytes()
    if digest(raw) != EXPECTED_SHA256[relative]:
        raise ValueError(f"descriptor hash is not safety-audited: {relative}")
    return path, raw, validate_policy_xml(path, relative, raw)


def run_one(root: Path, relative: str, temp_root: Path, interpreter: Path) -> dict[str, Any]:
    path, raw, fixtures = validate_descriptor(root, relative)
    temp_root.mkdir(parents=True, exist_ok=True)
    stage = temp_root / f"{path.parent.name}-{path.stem}"
    if stage.exists():
        raise ValueError("staging directory collision")
    stage.mkdir()
    staged_descriptor = stage / path.name
    shutil.copy2(path, staged_descriptor)
    if digest(staged_descriptor.read_bytes()) != EXPECTED_SHA256[relative]:
        raise ValueError(f"staged descriptor hash mismatch: {relative}")
    for source in fixtures:
        source_path = safe_source(path.parent, source)
        if source_path is None:
            continue
        staged_source = stage / source
        staged_source.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, staged_source)
        if digest(staged_source.read_bytes()) != fixtures[source]:
            raise ValueError(f"staged fixture hash mismatch: {relative}: {source}")
    env = {
        "PATH": os.defpath,
        "PYTHONPATH": str(root),
        "RUNTIME_ENVIRONMENT": "development",
        "TMPDIR": str(temp_root),
    }
    if not interpreter.is_file():
        raise ValueError(f"project interpreter missing: {interpreter}")
    result = subprocess.run(
        [str(interpreter), "-c", CHILD, str(staged_descriptor)],
        cwd=stage,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
        check=False,
    )
    marker = next(
        (
            line[len(RESULT_PREFIX):]
            for line in result.stdout.splitlines()
            if line.startswith(RESULT_PREFIX)
        ),
        None,
    )
    if result.returncode != 0 or marker is None:
        stderr = result.stderr.replace(str(root), "<checkout>").replace(
            str(temp_root), "<temp>"
        )
        raise RuntimeError(
            f"{relative}: child failed (exit {result.returncode}): {stderr[-1200:].strip()}"
        )
    record = json.loads(marker)
    if record.get("outcome") != "ok" or record.get("seeded") is not False:
        raise RuntimeError(
            f"{relative}: descriptor outcome {record.get('outcome')}; "
            f"{record.get('message', 'no error message')}"
        )
    return {
        "xml_sha256": digest(raw),
        "fixture_sha256_by_source": fixtures,
        "status": "CAPTURED",
        "seeded": False,
        "outcome": record["outcome"],
        "products": record.get("products", {}),
        "output_files": record.get("output_files", []),
    }


def self_check() -> None:
    with tempfile.TemporaryDirectory(prefix="dm-policy-self-check-") as temporary:
        root = Path(temporary)
        relative = ALLOWLIST[0]
        descriptor = root / relative
        descriptor.parent.mkdir(parents=True)
        parent = descriptor.parent
        (parent / "data").mkdir()
        (parent / "data/input.json").write_text("{}", encoding="utf-8")
        safe = descriptor
        safe.write_text(
            '<setup><generate source="data/input.json" target="ConsoleExporter"/></setup>',
            encoding="utf-8",
        )
        validate_policy_xml(
            safe, relative, safe.read_bytes(), audit_fixtures=False
        )
        for dangerous in (
            '<setup><execute/></setup>',
            '<setup><include file="other.xml"/></setup>',
            '<setup><generate script="x"/></setup>',
            '<setup><generate condition="true"/></setup>',
            '<setup><generate target="FileExporter"/></setup>',
            '<setup><generate source="../outside.json"/></setup>',
            '<setup><generate source="/etc/passwd"/></setup>',
        ):
            safe.write_text(dangerous, encoding="utf-8")
            try:
                validate_policy_xml(
                    safe, relative, safe.read_bytes(), audit_fixtures=False
                )
            except (ValueError, ET.ParseError):
                pass
            else:
                raise AssertionError(f"accepted dangerous XML: {dangerous}")
        (parent / "linked.json").symlink_to(parent / "data/input.json")
        safe.write_text('<setup><generate source="linked.json"/></setup>', encoding="utf-8")
        try:
            safe_source(parent, "linked.json")
        except ValueError:
            pass
        else:
            raise AssertionError("accepted symlinked source")
        safe.unlink()
        real_parent = descriptor.parent
        moved_parent = descriptor.parent.with_name(descriptor.parent.name + "-real")
        real_parent.rename(moved_parent)
        real_parent.symlink_to(moved_parent, target_is_directory=True)
        try:
            validate_descriptor(root, relative)
        except ValueError:
            pass
        else:
            raise AssertionError("accepted descriptor beneath symlinked parent")


def compare(frozen_root: Path, target_root: Path, interpreter: Path) -> dict[str, Any]:
    if (
        set(EXPECTED_SHA256) != set(ALLOWLIST)
        or len(ALLOWLIST) != 11
        or len(EXPECTED_FIXTURE_SHA256) != 4
    ):
        raise ValueError("static safety hash map does not match the 11-case allowlist")
    for relative in ALLOWLIST:
        before = validate_descriptor(frozen_root, relative)
        after = validate_descriptor(target_root, relative)
        if before[1] != after[1]:
            raise ValueError(f"descriptor bytes differ: {relative}")
    frozen_root = frozen_root.resolve()
    target_root = target_root.resolve()
    frozen_revision = revision(frozen_root)
    target_revision = revision(target_root)
    if frozen_revision != FROZEN_REVISION:
        raise ValueError("frozen checkout revision does not match the pinned baseline")
    if not clean_package_checkout(frozen_root) or not clean_package_checkout(target_root):
        raise ValueError("datamimic_ce has tracked or untracked changes in a comparison checkout")
    # Keep the venv path: resolving its python symlink drops the pyvenv.cfg context.
    interpreter = interpreter.absolute()
    interpreter_realpath = interpreter.resolve()
    if not interpreter.is_file():
        raise ValueError(f"project interpreter missing: {interpreter}")
    interpreter_version = subprocess.run(
        [str(interpreter), "--version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not interpreter_version:
        raise ValueError("child interpreter returned no version")
    with tempfile.TemporaryDirectory(prefix="dm-policy-compare-") as temporary:
        temp_root = Path(temporary)
        records = []
        for relative in ALLOWLIST:
            before = run_one(frozen_root, relative, temp_root / "frozen", interpreter)
            after = run_one(target_root, relative, temp_root / "target", interpreter)
            equal = equivalent(before, after)
            records.append({
                "path": relative,
                "frozen": before,
                "target": after,
                "equivalent": equal,
                "evidence_class": "normalized_unseeded" if equal else "DIFFERENT",
            })
        if revision(frozen_root) != frozen_revision or revision(target_root) != target_revision:
            raise ValueError("comparison checkout revision changed during comparison")
        if not clean_package_checkout(frozen_root) or not clean_package_checkout(target_root):
            raise ValueError("datamimic_ce changed during comparison")
        return {
            "frozen_root": str(frozen_root),
            "frozen_revision": frozen_revision,
            "target_root": str(target_root),
            "target_revision": target_revision,
            "child_interpreter": str(interpreter),
            "child_interpreter_realpath": str(interpreter_realpath),
            "child_interpreter_version": interpreter_version,
            "descriptors": records,
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frozen-root", type=Path, default=FROZEN_ROOT)
    parser.add_argument("--target-root", type=Path, default=TARGET_ROOT)
    parser.add_argument("--python", type=Path)
    parser.add_argument("--run", action="store_true", help="execute the allowlisted descriptors")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check()
        print("Policy-only comparator self-check passed")
        return
    if not args.run:
        parser.error("descriptor execution requires --run after review")
    interpreter = args.python or next(
        (
            root / ".venv/bin/python"
            for root in (args.target_root, args.frozen_root)
            if (root / ".venv/bin/python").is_file()
        ),
        None,
    )
    if interpreter is None and sys.prefix != sys.base_prefix:
        interpreter = Path(sys.executable)
    if interpreter is None:
        parser.error("checkout venvs are absent; pass the project interpreter with --python")
    report = compare(args.frozen_root, args.target_root, interpreter)
    print(json.dumps(report, sort_keys=True, indent=2))
    if any(not item["equivalent"] for item in report["descriptors"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
