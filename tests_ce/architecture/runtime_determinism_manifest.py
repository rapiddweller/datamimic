"""Generate and compare the cross-platform seeded runtime determinism manifest."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import TypedDict

EXPECTED_CONTENT_HASHES: dict[str, str] = {
    "address": "7d13e7a58d4a6258035436350ec7ecd043325ac46c5edbe039fa2797d4e169a0",
    "doctor": "2edec694c402cbc4f467858ea169a0888f5728ed2b7ce623632ee621e142c6a7",
    "patient": "906a07ea1c4d93ea52b2ba64139d2340e2d416c4b00a16e6448b61132bb93f89",
    "person": "e8365620df54a91427b02035004bf5315c637bde7e1df0706e1c641c857bd9d4",
}
EXPECTED_DSL_REPLAY_HASH = "b83a03232e6bbee270fa7a2a8fd48a80e6def81cff75f9e14f09cda7102cf650"
UTF8_PROBE_HASH = "346c09d6dbf788249cbd8cf5bae13bf2d4f34dd83e6aa689c190b996cf82d2a7"


class RuntimeDeterminismManifest(TypedDict):
    facade_hashes: dict[str, str]
    dsl_replay_hash: str
    utf8_probe_hash: str


def _dsl_replay_hash() -> str:
    repository = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "from tests_ce.integration_tests.test_determinism_seed_scenarios.test_determinism_seed_scenarios "
            "import replay_all_seeded_hash; print(replay_all_seeded_hash())",
        ],
        capture_output=True,
        check=True,
        cwd=repository,
        encoding="utf-8",
        text=True,
    )
    replay_hash = completed.stdout.strip()
    if not replay_hash:
        raise ValueError("seeded DSL replay produced no hash")
    return replay_hash


def _request(domain: str) -> dict[str, object]:
    return {
        "domain": domain,
        "version": "v1",
        "count": 3,
        "seed": "ci-determinism-gate",
        "locale": "en_US",
        "clock": "2026-01-01T00:00:00Z",
    }


def build_actual_manifest() -> RuntimeDeterminismManifest:
    from datamimic_ce.domains.determinism import canonical_json, hash_bytes
    from datamimic_ce.domains.facade import REGISTRY, generate_domain

    hashes: dict[str, str] = {}
    for domain in sorted({key[0] for key in REGISTRY}):
        response = generate_domain(_request(domain))
        proof = response.get("determinism_proof")
        if not isinstance(proof, dict):
            raise ValueError(f"Facade domain {domain!r} returned no determinism proof")
        content_hash = proof.get("content_hash")
        if not isinstance(content_hash, str):
            raise ValueError(f"Facade domain {domain!r} returned no content hash")
        hashes[domain] = content_hash

    probe = hash_bytes(canonical_json({"probe": "Grüße 世界 — UTF-8"}))
    return {"facade_hashes": hashes, "dsl_replay_hash": _dsl_replay_hash(), "utf8_probe_hash": probe}


def write_manifest(path: Path) -> None:
    path.write_text(
        json.dumps(build_actual_manifest(), sort_keys=True, ensure_ascii=False) + "\n",
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
    dsl_replay_hash: object = payload.get("dsl_replay_hash")
    utf8_probe_hash: object = payload.get("utf8_probe_hash")
    if not isinstance(dsl_replay_hash, str):
        raise ValueError(f"{path} has no string dsl_replay_hash")
    if not isinstance(utf8_probe_hash, str):
        raise ValueError(f"{path} has no string utf8_probe_hash")
    return {
        "facade_hashes": _read_string_map(facade_hashes, f"{path}.facade_hashes"),
        "dsl_replay_hash": dsl_replay_hash,
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

    for domain, expected_hash in EXPECTED_CONTENT_HASHES.items():
        actual_hash = baseline["facade_hashes"].get(domain)
        if actual_hash != expected_hash:
            errors.append(f"{domain}: actual hash does not match committed golden")
    if baseline["utf8_probe_hash"] != UTF8_PROBE_HASH:
        errors.append("utf8 probe hash does not match the committed UTF-8 golden")
    if baseline["dsl_replay_hash"] != EXPECTED_DSL_REPLAY_HASH:
        errors.append("DSL replay hash does not match the committed golden")
    return tuple(errors)


def _write_summary(manifests: Mapping[str, RuntimeDeterminismManifest], errors: tuple[str, ...]) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path is None:
        return
    status = "PASS" if not errors else "FAIL"
    headers = [*EXPECTED_CONTENT_HASHES, "dsl_replay_all_seeded", "utf8_probe"]
    lines = [
        "## Seeded runtime determinism hash fan-in",
        "",
        f"**{status}** — compared {len(manifests)} actual manifests directly.",
        "",
        f"| Cell | {' | '.join(headers)} |",
        f"| --- | {' | '.join('---' for _ in headers)} |",
    ]
    for label, manifest in manifests.items():
        values = [manifest["facade_hashes"].get(domain, "<missing>") for domain in EXPECTED_CONTENT_HASHES]
        values.append(manifest["dsl_replay_hash"])
        values.append(manifest["utf8_probe_hash"])
        lines.append(f"| `{label}` | {' | '.join(f'`{value}`' for value in values)} |")
    golden_values = [*EXPECTED_CONTENT_HASHES.values(), EXPECTED_DSL_REPLAY_HASH, UTF8_PROBE_HASH]
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
        _write_summary({}, errors)
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    manifests = {path.parent.name: read_manifest(path) for path in paths}
    errors = compare_manifests(manifests)
    print(f"Compared {len(manifests)} actual seeded runtime determinism manifests directly.")
    for label, manifest in manifests.items():
        print(f"{label}: {json.dumps(manifest, sort_keys=True)}")
    _write_summary(manifests, errors)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("All actual facade and DSL replay hashes match each other and the committed goldens.")
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
