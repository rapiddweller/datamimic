"""Generate and compare the cross-platform seeded runtime determinism manifest."""

from __future__ import annotations

import argparse
import json
import os
import re
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from pathlib import Path
from typing import TypedDict

EXPECTED_FACADE_CONTENT_HASHES: dict[str, str] = {
    "address": "7d13e7a58d4a6258035436350ec7ecd043325ac46c5edbe039fa2797d4e169a0",
    "doctor": "2edec694c402cbc4f467858ea169a0888f5728ed2b7ce623632ee621e142c6a7",
    "patient": "906a07ea1c4d93ea52b2ba64139d2340e2d416c4b00a16e6448b61132bb93f89",
    "person": "e8365620df54a91427b02035004bf5315c637bde7e1df0706e1c641c857bd9d4",
}
EXPECTED_ENTITY_REPLAY_HASH = "749dc011672c1287823ae6fff20a8cc0bf42031faf114bd70d9abd6142b8af89"
EXPECTED_LITERAL_REPLAY_HASH = "08a79c02067e4e3d8f93a7434c6196ff5ef0da5b2bf811ca7174f65ed8557185"
UTF8_PROBE_HASH = "346c09d6dbf788249cbd8cf5bae13bf2d4f34dd83e6aa689c190b996cf82d2a7"


class RuntimeDeterminismManifest(TypedDict):
    facade_hashes: dict[str, str]
    entity_replay_hash: str
    literal_replay_hash: str
    coverage: dict[str, str]
    utf8_probe_hash: str


def build_actual_manifest() -> RuntimeDeterminismManifest:
    from datamimic_ce.domains.determinism import canonical_json, hash_bytes
    from datamimic_ce.domains.domain_core.entity_registry import list_entity_specs
    from datamimic_ce.domains.domain_core.generator_registry import generator_namespace
    from datamimic_ce.domains.facade import REGISTRY, generate_domain
    from tests_ce.integration_tests.test_determinism_seed_scenarios.test_determinism_seed_scenarios import (
        seeded_model_hash,
    )

    hashes: dict[str, str] = {}
    for domain in sorted({key[0] for key in REGISTRY}):
        response = generate_domain(
            {
                "domain": domain,
                "version": "v1",
                "count": 3,
                "seed": "ci-determinism-gate",
                "locale": "en_US",
                "clock": "2026-01-01T00:00:00Z",
            }
        )
        proof = response.get("determinism_proof")
        if not isinstance(proof, dict):
            raise ValueError(f"Facade domain {domain!r} returned no determinism proof")
        content_hash = proof.get("content_hash")
        if not isinstance(content_hash, str):
            raise ValueError(f"Facade domain {domain!r} returned no content hash")
        hashes[domain] = content_hash

    test_dir = Path(__file__).resolve().parents[2] / "tests_ce/integration_tests/test_determinism_seed_scenarios"
    entity_root = ET.parse(test_dir / "seed_in_setup.xml").getroot()
    literal_root = ET.parse(test_dir / "replay_all_seeded.xml").getroot()
    literal_generators = {
        value.split("(", 1)[0]
        for key in literal_root.findall("generate[@name='literal']/key")
        if (value := key.get("generator")) is not None
    }
    script_paths = literal_root.findall("generate[@name='script']/key")
    dynamic_families = sorted(
        {
            family
            for key in script_paths
            for family in re.findall(r"\b(random|uuid|fake|datetime|pd|math|np)\b", key.get("script", ""))
        }
    )
    coverage = {
        "Facade API": f"{len(hashes)}/{len(EXPECTED_FACADE_CONTENT_HASHES)}",
        "Entities": f"{len(entity_root.findall('generate'))}/{len(list_entity_specs())} (selected attributes)",
        "Literal generators": (
            f"{len(literal_generators)}/{len(generator_namespace())} "
            "(SequenceTableGenerator covered by external-service DSL tests; excluded from this byte hash: DB state)"
        ),
        "Dynamic seeded Safe Globals": f"{len(script_paths)} representative paths ({', '.join(dynamic_families)})",
        "UTF-8 probe": "1 (canonical UTF-8 probe)",
    }
    probe = hash_bytes(canonical_json({"probe": "Grüße 世界 — UTF-8"}))
    return {
        "facade_hashes": hashes,
        "entity_replay_hash": seeded_model_hash("seed_in_setup.xml"),
        "literal_replay_hash": seeded_model_hash("replay_all_seeded.xml"),
        "coverage": coverage,
        "utf8_probe_hash": probe,
    }


def write_manifest(path: Path) -> None:
    path.write_text(
        json.dumps(build_actual_manifest(), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _read_string_map(value: object, label: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    result: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str):
            raise ValueError(f"{label} must contain only string keys and values")
        result[key] = item
    return result


def read_manifest(path: Path) -> RuntimeDeterminismManifest:
    payload: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    facade_hashes: object = payload.get("facade_hashes")
    entity_replay_hash: object = payload.get("entity_replay_hash")
    literal_replay_hash: object = payload.get("literal_replay_hash")
    coverage: object = payload.get("coverage")
    utf8_probe_hash: object = payload.get("utf8_probe_hash")
    if not isinstance(entity_replay_hash, str):
        raise ValueError(f"{path} has no string entity_replay_hash")
    if not isinstance(literal_replay_hash, str):
        raise ValueError(f"{path} has no string literal_replay_hash")
    if not isinstance(utf8_probe_hash, str):
        raise ValueError(f"{path} has no string utf8_probe_hash")
    return {
        "facade_hashes": _read_string_map(facade_hashes, f"{path}.facade_hashes"),
        "entity_replay_hash": entity_replay_hash,
        "literal_replay_hash": literal_replay_hash,
        "coverage": _read_string_map(coverage, f"{path}.coverage"),
        "utf8_probe_hash": utf8_probe_hash,
    }


def compare_manifests(manifests: Mapping[str, RuntimeDeterminismManifest]) -> tuple[str, ...]:
    errors: list[str] = []
    if not manifests:
        return ("no runtime determinism manifests found",)

    baseline_label, baseline = next(iter(manifests.items()))
    for label, manifest in manifests.items():
        if manifest != baseline:
            errors.append(f"{label}: actual hashes differ from {baseline_label}")

    for domain, expected_hash in EXPECTED_FACADE_CONTENT_HASHES.items():
        actual_hash = baseline["facade_hashes"].get(domain)
        if actual_hash != expected_hash:
            errors.append(f"{domain}: actual hash does not match committed golden")
    if baseline["utf8_probe_hash"] != UTF8_PROBE_HASH:
        errors.append("utf8 probe hash does not match the committed UTF-8 golden")
    if baseline["entity_replay_hash"] != EXPECTED_ENTITY_REPLAY_HASH:
        errors.append("seed_in_setup.xml hash does not match the committed golden")
    if baseline["literal_replay_hash"] != EXPECTED_LITERAL_REPLAY_HASH:
        errors.append("replay_all_seeded.xml hash does not match the committed golden")
    return tuple(errors)


def _write_summary(
    manifests: Mapping[str, RuntimeDeterminismManifest], errors: tuple[str, ...], expected_count: int
) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path is None:
        return
    status = "PASS" if not errors else "FAIL"
    coverage_rows = (
        [f"| {name} | {value} |" for name, value in next(iter(manifests.values()))["coverage"].items()]
        if manifests
        else ["| unavailable | |"]
    )
    lines = [
        "## Seeded runtime determinism hash fan-in",
        "",
        f"**{len(manifests)}/{expected_count} {status}** — compared actual manifests directly.",
        "",
        "### Coverage",
        "",
        "| Contract | Coverage |",
        "| --- | --- |",
        *coverage_rows,
        "",
        "Full SHA-256 values are in the job log and artifacts.",
        "",
        "### DSL runtime",
        "",
        "| Cell | entity_replay | literal_replay | utf8_probe |",
        "| --- | --- | --- | --- |",
    ]
    for label, manifest in manifests.items():
        values = [
            manifest["entity_replay_hash"][:12],
            manifest["literal_replay_hash"][:12],
            manifest["utf8_probe_hash"][:12],
        ]
        lines.append(f"| `{label}` | {' | '.join(f'`{value}`' for value in values)} |")
    golden_values = [EXPECTED_ENTITY_REPLAY_HASH[:12], EXPECTED_LITERAL_REPLAY_HASH[:12], UTF8_PROBE_HASH[:12]]
    lines.append(f"| `committed-golden` | {' | '.join(f'`{value}`' for value in golden_values)} |")
    lines.extend(
        [
            "",
            "### Facade API",
            "",
            f"| Cell | {' | '.join(EXPECTED_FACADE_CONTENT_HASHES)} |",
            f"| --- | {' | '.join('---' for _ in EXPECTED_FACADE_CONTENT_HASHES)} |",
        ]
    )
    for label, manifest in manifests.items():
        values = [manifest["facade_hashes"].get(domain, "<missing>")[:12] for domain in EXPECTED_FACADE_CONTENT_HASHES]
        lines.append(f"| `{label}` | {' | '.join(f'`{value}`' for value in values)} |")
    golden_values = [value[:12] for value in EXPECTED_FACADE_CONTENT_HASHES.values()]
    lines.append(f"| `committed-golden` | {' | '.join(f'`{value}`' for value in golden_values)} |")
    if errors:
        lines.extend(["", "Errors:", *[f"- {error}" for error in errors]])
    with Path(summary_path).open("a", encoding="utf-8") as summary:
        summary.write("\n".join(lines) + "\n")


def _generate_command(output: Path) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    write_manifest(output)
    print(f"Wrote seeded runtime determinism manifest: {output}")
    return 0


def _compare_command(root: Path, expected_count: int) -> int:
    paths = sorted(root.rglob("runtime-determinism-manifest.json"))
    if len(paths) != expected_count:
        errors: tuple[str, ...] = (f"expected {expected_count} manifests, found {len(paths)}",)
        _write_summary({}, errors, expected_count)
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    manifests = {path.parent.name: read_manifest(path) for path in paths}
    errors = compare_manifests(manifests)
    print(f"Compared {len(manifests)}/{expected_count} actual seeded runtime determinism manifests directly.")
    print("Coverage:")
    if manifests:
        coverage = next(iter(manifests.values()))["coverage"]
        for name, value in coverage.items():
            print(f"- {name}: {value}")
    print("Hashes:")
    for label, manifest in manifests.items():
        facade_hashes = ",".join(manifest["facade_hashes"].values())
        print(
            f"{label}: entity={manifest['entity_replay_hash']} literal={manifest['literal_replay_hash']} "
            f"facade={facade_hashes} utf8={manifest['utf8_probe_hash']}"
        )
    _write_summary(manifests, errors, expected_count)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(
        f"{len(manifests)}/{expected_count} PASS: "
        "all actual runtime hashes match each other and the committed goldens."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate = subparsers.add_parser("generate")
    generate.add_argument("--output", type=Path, required=True)
    compare = subparsers.add_parser("compare")
    compare.add_argument("--root", type=Path, required=True)
    compare.add_argument("--expected-count", type=int, required=True)
    args = parser.parse_args()
    if args.command == "generate":
        return _generate_command(args.output)
    return _compare_command(args.root, args.expected_count)


if __name__ == "__main__":
    raise SystemExit(main())
