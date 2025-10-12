"""Verify component loader relies on dataset_path (rule 3)."""
import datamimic_ce.domains.common.profile_components as profile_components
from datamimic_ce.domains.facade import generate_domain


def test_component_loader_uses_dataset_path(monkeypatch) -> None:
    calls: list[tuple] = []
    original = profile_components.dataset_path

    def tracking_dataset_path(*args, **kwargs):
        calls.append(args)
        return original(*args, **kwargs)

    monkeypatch.setattr(profile_components, "dataset_path", tracking_dataset_path)
    profile_components._component_rows.cache_clear()

    generate_domain(
        {
            "domain": "person",
            "version": "v1",
            "count": 1,
            "seed": "dataset-path",
            "locale": "en_US",
            "clock": "2025-01-01T00:00:00Z",
            "component_id": "urban_adult",
        }
    )

    assert calls
