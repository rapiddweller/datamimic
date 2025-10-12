"""Strict-mode regression tests for component resolution (rules 3-4)."""
import pytest

from datamimic_ce.domains.exceptions import DomainError
from datamimic_ce.domains.facade import generate_domain


def test_unknown_component_strict_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATAMIMIC_STRICT_DATASET", "1")
    req = {
        "domain": "person",
        "version": "v1",
        "count": 1,
        "seed": "strict-component",
        "locale": "en_US",
        "clock": "2025-01-01T00:00:00Z",
        "component_id": "missing_component",
    }
    with pytest.raises(DomainError) as excinfo:
        generate_domain(req)
    assert excinfo.value.code == "unknown_component"
