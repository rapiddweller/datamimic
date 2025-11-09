"""Unit tests for MCP argument models."""

import pytest

from datamimic_ce.mcp import models
from datamimic_ce.mcp.models import GenerateArgs, MAX_COUNT


def test_mutually_exclusive_profile_and_component() -> None:
    with pytest.raises(ValueError):
        GenerateArgs(domain="person", profile_id="p", component_id="c")


def test_count_upper_bound() -> None:
    with pytest.raises(ValueError):
        GenerateArgs(domain="person", count=MAX_COUNT + 1)


def test_dataset_resolves_locale() -> None:
    args = GenerateArgs(domain="person", dataset="us")
    assert args.dataset == "US"
    assert args.locale == "en_US"


def test_dataset_locale_inferred_from_metadata(monkeypatch) -> None:
    models._default_locale_for_dataset.cache_clear()
    monkeypatch.setattr(
        models,
        "_DATASET_LOCALE_DEFAULTS",
        {"US": "en_US", "VN": "vi_VN"},
        raising=False,
    )
    args = GenerateArgs(domain="person", dataset="DE")
    assert args.locale == "de_DE"


def test_dataset_locale_mismatch() -> None:
    with pytest.raises(ValueError):
        GenerateArgs(domain="person", dataset="US", locale="de_DE")


def test_to_payload_expands_defaults() -> None:
    args = GenerateArgs(domain="person", locale="en_US", constraints={"age": {"min": 18}})
    payload = args.to_payload()
    assert payload["constraints"] == {"age": {"min": 18}}
    assert payload["clock"] == args.clock
