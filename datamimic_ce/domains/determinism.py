from __future__ import annotations

import hashlib
import json
import random
import uuid
from collections.abc import Iterable
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def canonicalize(obj: Any) -> Any:
    """Recursively sort mapping keys for deterministic JSON output."""
    if is_dataclass(obj):
        # mypy: is_dataclass() is a runtime predicate and doesn't narrow to
        # DataclassInstance; asdict expects a dataclass instance. Safe at runtime.
        obj = asdict(obj)  # type: ignore[arg-type]
    if isinstance(obj, dict):
        return {key: canonicalize(obj[key]) for key in sorted(obj)}
    if isinstance(obj, list):
        return [canonicalize(item) for item in obj]
    return obj


def canonical_json(obj: Any) -> bytes:
    canonical = canonicalize(obj)
    return json.dumps(canonical, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_uuid(namespace: str, *parts: Any) -> str:
    base_uuid = uuid.uuid5(uuid.NAMESPACE_URL, namespace)
    name = "::".join(str(part) for part in parts)
    return str(uuid.uuid5(base_uuid, name))


def derive_seed(seed_any: Any) -> int:
    if isinstance(seed_any, int):
        return seed_any
    if isinstance(seed_any, str) and seed_any.isdigit():
        return int(seed_any)
    digest = hashlib.sha256(str(seed_any).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def mix_seed(seed: int, *parts: Any) -> int:
    components: Iterable[str] = [str(seed), *[str(part) for part in parts]]
    digest = hashlib.sha256("::".join(components).encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def derive_profile_seed(domain: str, profile_id: str, facet: str) -> int:
    """Mix profile metadata into deterministic seeds (rule 4)."""

    base = derive_seed(f"{domain}:{facet}")
    return mix_seed(base, profile_id)


def compute_provenance_hash(paths: Iterable[str]) -> str:
    """Return a SHA-256 hash capturing the provenance of the provided files."""

    digest = hashlib.sha256()
    for raw_path in sorted(paths):
        path = Path(raw_path)
        digest.update(path.as_posix().encode("utf-8"))
        if path.exists():
            digest.update(path.read_bytes())
        else:
            digest.update(b"<missing>")
    return digest.hexdigest()


def frozen_clock(iso_datetime: str) -> datetime:
    normalized = iso_datetime.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class RandomLike(random.Random):
    """Wrapper around random.Random to make the dependency explicit."""


def with_rng(seed: int) -> RandomLike:
    rng = RandomLike()
    rng.seed(seed, version=2)
    return rng
