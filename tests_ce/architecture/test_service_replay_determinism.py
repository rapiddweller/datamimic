"""Service-level replay determinism gate.

The test that would have caught the original CreditCardService.bic/bin
drift. For every domain service we know about, it constructs two
instances with the same seeded ``random.Random`` and asserts that the
full attribute graph of the generated entity is byte-identical.

Recursive comparison handles nested entities (e.g. Bank inside
CreditCard) without falling back to ``repr`` (which would leak memory
addresses and report false positives).

This is the empirical determinism contract for direct-Service usage in
CE: pass a seeded RNG, get deterministic output across every public
attribute.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from random import Random

import pytest

# All CE domain services that wrap a single entity. Listed explicitly so a
# missing service is a visible PR change, not a discovery side-effect.
from datamimic_ce.domains.ecommerce.services import OrderService, ProductService
from datamimic_ce.domains.finance.services import (
    BankAccountService,
    BankService,
    CreditCardService,
    TransactionService,
)
from datamimic_ce.domains.healthcare.services import (
    DoctorService,
    HospitalService,
    MedicalDeviceService,
    MedicalProcedureService,
    PatientService,
)
from datamimic_ce.domains.insurance.services import (
    InsuranceCompanyService,
    InsuranceCoverageService,
    InsurancePolicyService,
    InsuranceProductService,
)
from datamimic_ce.domains.public_sector.services import (
    AdministrationOfficeService,
    EducationalInstitutionService,
    PoliceOfficerService,
)

SEED = 20260519

SERVICES_WITHOUT_DATASET: list[type] = [
    BankService,
    BankAccountService,
    CreditCardService,
    TransactionService,
    PatientService,
    DoctorService,
    HospitalService,
    MedicalDeviceService,
    MedicalProcedureService,
    InsuranceCompanyService,
    InsuranceProductService,
    InsuranceCoverageService,
    InsurancePolicyService,
    OrderService,
    ProductService,
    AdministrationOfficeService,
    EducationalInstitutionService,
    PoliceOfficerService,
]


def _normalise(value, depth: int = 0, max_depth: int = 8):
    """Recursive normalise to a JSON-shaped value.

    Falls back to ``str(type(value).__name__)`` only when we cannot
    extract any public attributes. We never call ``repr`` so memory
    addresses don't pollute the diff.
    """
    if depth > max_depth:
        return "<max-depth>"
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [_normalise(item, depth + 1) for item in value]
    if isinstance(value, dict):
        return {str(k): _normalise(v, depth + 1) for k, v in value.items()}
    if hasattr(value, "model_dump"):
        try:
            return value.model_dump(mode="json")
        except Exception:  # pragma: no cover — fall through to attribute walk
            pass
    attrs = {}
    for name in dir(value):
        if name.startswith("_"):
            continue
        try:
            attr = getattr(value, name)
        except Exception:
            continue
        if callable(attr):
            continue
        attrs[name] = _normalise(attr, depth + 1)
    return attrs if attrs else type(value).__name__


def _instantiate(cls: type, *, rng: Random):
    """Construct the service with the rng arg the codebase accepts."""
    return cls(rng=rng)


@pytest.mark.parametrize("service_cls", SERVICES_WITHOUT_DATASET, ids=lambda c: c.__name__)
def test_service_replay_byte_identical_under_seeded_rng(service_cls: type) -> None:
    """Two services constructed with identical seeded RNGs must produce
    byte-identical entity payloads, attribute by attribute."""
    a = _instantiate(service_cls, rng=Random(SEED))
    b = _instantiate(service_cls, rng=Random(SEED))

    out_a = _normalise(a.generate())
    out_b = _normalise(b.generate())

    # Use JSON for an order-independent diff that still shows the divergent keys.
    serialised_a = json.dumps(out_a, sort_keys=True, default=str)
    serialised_b = json.dumps(out_b, sort_keys=True, default=str)

    if serialised_a != serialised_b:
        # Find the diverging keys so a regression is debuggable in CI logs.
        if isinstance(out_a, dict) and isinstance(out_b, dict):
            diffs = []
            for key in sorted(set(out_a) | set(out_b)):
                if out_a.get(key) != out_b.get(key):
                    diffs.append((key, out_a.get(key), out_b.get(key)))
            divergence = "\n".join(
                f"  {key}: a={a_val!r}  ≠  b={b_val!r}" for key, a_val, b_val in diffs[:10]
            )
        else:
            divergence = f"  a={serialised_a[:200]}\n  b={serialised_b[:200]}"
        pytest.fail(
            f"{service_cls.__name__} breaks the CE replay determinism contract.\n"
            f"Two instances seeded with Random({SEED}) produced divergent output:\n"
            f"{divergence}"
        )


@pytest.mark.parametrize("service_cls", SERVICES_WITHOUT_DATASET, ids=lambda c: c.__name__)
def test_service_replay_diverges_under_different_seeds(service_cls: type) -> None:
    """Sanity check: different seeds must produce different output."""
    a = _instantiate(service_cls, rng=Random(SEED))
    b = _instantiate(service_cls, rng=Random(SEED + 1))

    out_a = _normalise(a.generate())
    out_b = _normalise(b.generate())

    assert out_a != out_b, (
        f"{service_cls.__name__} produced identical output under different seeds — "
        f"its RNG path is not wired through."
    )
