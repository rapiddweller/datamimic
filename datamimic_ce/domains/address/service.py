from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..determinism import canonical_json, derive_seed, hash_bytes, mix_seed, stable_uuid, with_rng
from ..exceptions import DomainError
from ..locales import SUPPORTED_DATASET_CODES, load_locale


@dataclass(frozen=True)
class AddressRequest:
    domain: str = "address"
    version: str = "v1"
    count: int = 1
    seed: str | int = "0"
    locale: str = "en_US"
    constraints: dict[str, Any] = field(default_factory=dict)
    clock: str = "2025-01-01T00:00:00Z"
    request_hash: str = ""


def _apply_postal_prefix(code: str, prefix: str) -> str:
    if len(prefix) > len(code):
        raise ValueError("Postal prefix longer than generated code")
    if not code.startswith(prefix):
        return prefix + code[len(prefix) :]
    return code


def _format_postal_code(pattern: str, rng) -> str:
    digits = []
    for char in pattern:
        if char == "#":
            digits.append(str(rng.randrange(0, 10)))
        else:
            digits.append(char)
    return "".join(digits)


def generate(req: AddressRequest) -> dict[str, Any]:
    if req.count < 0:
        raise DomainError(
            code="invalid_count",
            message="Count must be non-negative",
            hint="Provide a count >= 0",
            path="/count",
            request_hash=req.request_hash,
        )

    try:
        locale_pack = load_locale(req.locale, req.version)
    except ValueError as exc:
        hint_codes = ", ".join(SUPPORTED_DATASET_CODES) or "<none>"
        raise DomainError(
            code="unsupported_locale",
            message=str(exc),
            hint=f"Choose a locale mapping to dataset codes: {hint_codes}",
            path="/locale",
            request_hash=req.request_hash,
        ) from exc
    constraints = req.constraints or {}
    address_locale = locale_pack.address

    if "country" in constraints and constraints["country"] != address_locale["country_code"]:
        raise DomainError(
            code="invalid_constraints",
            message="constraints.country must match the locale country code",
            hint=f"Use {address_locale['country_code']}",
            path="/constraints/country",
            request_hash=req.request_hash,
        )

    derived_seed = derive_seed(req.seed)
    items: list[dict[str, Any]] = []

    for index in range(req.count):
        item_seed = mix_seed(derived_seed, index)
        rng = with_rng(item_seed)
        street = address_locale["street_names"][rng.randrange(len(address_locale["street_names"]))]
        house_number = rng.randint(10, 199)
        city = address_locale["cities"][index % len(address_locale["cities"])]
        state = address_locale["states"][index % len(address_locale["states"])]
        postal = _format_postal_code(address_locale["postal_code_format"], rng)
        postal_prefix = constraints.get("postal_code_prefix")
        if postal_prefix:
            try:
                postal = _apply_postal_prefix(postal, str(postal_prefix))
            except ValueError as exc:
                raise DomainError(
                    code="invalid_constraints",
                    message=str(exc),
                    hint="Ensure the postal_code_prefix is shorter than the format",
                    path="/constraints/postal_code_prefix",
                    request_hash=req.request_hash,
                ) from exc

        address_id = stable_uuid("datamimic:address:v1", derived_seed, index)
        line1 = f"{house_number} {street}"
        formatted = f"{line1}, {city}, {state} {postal}, {address_locale['country_code']}"

        items.append(
            {
                "id": address_id,
                "human_id": f"ADR-{address_id[:8].upper()}",
                "line1": line1,
                "city": city,
                "state": state,
                "postal_code": postal,
                "country": address_locale["country_code"],
                "locale": req.locale,
                "formatted": formatted,
            }
        )

    items_hash = hash_bytes(canonical_json(items))

    return {
        "domain": req.domain,
        "version": req.version,
        "request_hash": req.request_hash,
        "items": items,
        "determinism_proof": {
            "algorithm": "uuid5+sha256",
            "seed_canonical": str(derived_seed),
            "content_hash": items_hash,
        },
    }
