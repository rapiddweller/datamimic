"""Distribution checks for component-driven constraints (rules 4-6)."""
from datamimic_ce.domains.facade import generate_domain


def _ages(response: dict) -> list[int]:
    return [item["age"] for item in response["items"]]


def test_component_adjusts_age_band() -> None:
    baseline = generate_domain(
        {
            "domain": "person",
            "version": "v1",
            "count": 6,
            "seed": "distribution-test",
            "locale": "en_US",
            "clock": "2025-01-01T00:00:00Z",
        }
    )

    profiled = generate_domain(
        {
            "domain": "person",
            "version": "v1",
            "count": 6,
            "seed": "distribution-test",
            "locale": "en_US",
            "clock": "2025-01-01T00:00:00Z",
            "component_id": "urban_adult",
        }
    )

    baseline_ages = _ages(baseline)
    profiled_ages = _ages(profiled)

    assert any(age < 25 or age > 45 for age in baseline_ages)
    assert all(25 <= age <= 45 for age in profiled_ages)
