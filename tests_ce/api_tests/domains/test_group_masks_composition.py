"""Unit tests for group mask composition utilities."""

from __future__ import annotations

import pytest

from datamimic_ce.domains.common.demographics.sampler import compose_weights, load_group_table


def test_compose_weights_basic_normalization() -> None:
    base = {"A": 0.6, "B": 0.4}
    mask = {"A": 0.8, "B": 0.2}
    result = compose_weights(base, mask)
    assert pytest.approx(sum(result.values()), rel=0, abs=1e-9) == 1.0
    assert result["A"] > result["B"]


def test_compose_weights_missing_keys_retain_base() -> None:
    base = {"A": 0.7, "B": 0.3}
    mask = {"A": 0.5}
    result = compose_weights(base, mask)
    assert result == {"A": pytest.approx(1.0)}


def test_load_group_table_normalizes_rows() -> None:
    mask, provenance = load_group_table("US", "v1", "age_band", "age_18_44")
    assert provenance is not None
    assert pytest.approx(sum(mask.values()), rel=0, abs=1e-9) == 1.0
    assert mask == {(18, 44): pytest.approx(1.0)}
