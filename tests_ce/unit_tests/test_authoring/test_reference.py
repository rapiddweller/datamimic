# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.

"""Reference projections remain derived from canonical registries and models."""

import json

import pytest

from datamimic_ce.authoring.reference import (
    ReferenceTopic,
    capabilities_index,
    capabilities_manifest,
    capabilities_sections,
    generator_names,
    known_generator_names,
    reference,
)
from datamimic_ce.authoring.schema import build_schema_index
from datamimic_ce.authoring.spec import authoring_spec_json_schema
from datamimic_ce.enums.converter_enums import ConverterEnum
from datamimic_ce.exporters.exporter_util import buffered_exporter_names
from datamimic_ce.model.element_registry import list_element_tags


def test_overview_is_owned_prose_over_live_topics() -> None:
    text = reference(ReferenceTopic.OVERVIEW)
    assert "AuthoringSpecV1" in text
    assert all(topic.value in text for topic in ReferenceTopic)


def test_reference_and_capabilities_project_live_intent_schema() -> None:
    schema = authoring_spec_json_schema()
    assert capabilities_manifest()["authoring_spec"] == schema
    assert '"AuthoringSpecV1"' in reference(ReferenceTopic.SCAFFOLD)


def test_reference_timeseries_documents_ts_namespace() -> None:
    text = reference(ReferenceTopic.TIMESERIES)
    assert "ts.now" in text and "ts.step" in text and "ts.series" in text


def test_reference_converters_come_from_enum() -> None:
    text = reference(ReferenceTopic.CONVERTERS)
    assert all(member.value in text for member in ConverterEnum)


def test_reference_targets_come_from_registry() -> None:
    text = reference(ReferenceTopic.TARGETS)
    assert all(name in text for name in buffered_exporter_names())


def test_element_reference_uses_registered_schema() -> None:
    text = reference(ReferenceTopic.ELEMENT, "generate")
    assert "Attributes:" in text and "Children:" in text
    with pytest.raises(ValueError, match="Unknown element"):
        reference(ReferenceTopic.ELEMENT, "generat")


def test_schema_index_covers_runtime_element_registry() -> None:
    assert set(list_element_tags()) <= set(build_schema_index().tags)


def test_reference_context_documents_scope_aliases() -> None:
    text = reference(ReferenceTopic.CONTEXT).lower()
    assert "this." in text and "parent." in text and "root." in text


# ---------------------------------------------------------------------------
# Compact capabilities contract — Completeness, Fidelity, Budget
# ---------------------------------------------------------------------------


def test_compact_completeness_matches_full_manifest() -> None:
    compact = capabilities_index()
    full = capabilities_manifest()

    # Element tags are the same set
    assert set(compact["elements"]) == set(full["elements"])
    for tag, el in compact["elements"].items():
        # Attribute names match (compact has sorted names, full has dict keys)
        assert set(el["attributes"]) == set(full["elements"][tag]["attributes"])
        # Children are verbatim
        assert el["children"] == full["elements"][tag]["children"]

    # Rule ids match and stay in manifest order
    assert [r["id"] for r in compact["rules"]] == [r["id"] for r in full["rules"]]

    # Compact sections == manifest key order
    assert compact["_meta"]["sections"] == list(capabilities_manifest())

    # Other name arrays are verbatim
    for section in ("generators", "entities", "converters", "distributions",
                    "numeric_distributions", "finite_numeric_sequences"):
        assert compact[section] == full[section]

    # Source capabilities and targets are verbatim
    assert compact["source_capabilities"] == full["source_capabilities"]
    assert compact["targets"] == full["targets"]
    assert compact["aliases"] == full["aliases"]


def test_compact_fidelity_full_mode_equals_manifest() -> None:
    """--full provides the exact capabilities_manifest() output."""
    full = capabilities_manifest()
    assert capabilities_manifest() == full  # idempotent


def test_compact_fidelity_section_mode() -> None:
    result = capabilities_sections(("elements",))
    assert set(result) == {"elements"}
    assert result["elements"] == capabilities_manifest()["elements"]

    result = capabilities_sections(("rules", "schema_version"))
    assert set(result) == {"rules", "schema_version"}
    assert result["rules"] == capabilities_manifest()["rules"]


def test_compact_budget_under_25kb_and_20_percent_of_full() -> None:
    compact_json = json.dumps(capabilities_index())
    full_json = json.dumps(capabilities_manifest())
    compact_bytes = len(compact_json.encode())
    full_bytes = len(full_json.encode())
    assert compact_bytes < 25_000
    assert compact_bytes <= full_bytes * 0.20


def test_compact_sections_rejects_unknown_section() -> None:
    with pytest.raises(ValueError, match="Unknown capability section"):
        capabilities_sections(("bogus",))
    # Atomic: valid+invalid together should fail
    with pytest.raises(ValueError, match="Unknown capability section"):
        capabilities_sections(("elements", "bogus"))


def test_compact_sections_unknown_error_carries_valid_sections() -> None:
    from datamimic_ce.authoring.contracts import UnknownCapabilitySection

    with pytest.raises(UnknownCapabilitySection) as exc_info:
        capabilities_sections(("bogus",))
    assert isinstance(exc_info.value.valid_sections, list)
    assert "elements" in exc_info.value.valid_sections


def test_generator_names_is_unbounded_and_deterministic() -> None:
    """known_generator_names no longer parses clip()-ed prose text."""
    names = known_generator_names()
    assert isinstance(names, set)
    assert len(names) > 0
    # Repeatable
    assert names == known_generator_names()
    # generator_names() returns the same set
    assert names == generator_names()


def test_element_reference_pages_not_truncated() -> None:
    """Every element detail page fits within the 16k clip limit."""
    for tag in build_schema_index().tags:
        text = reference(ReferenceTopic.ELEMENT, tag)
        assert "[truncated" not in text, f"<{tag}> element reference is truncated"


def test_capabilities_cli_compact_is_valid_json() -> None:
    """The compact output is parseable, versioned, and omits authoring_spec."""
    from typer.testing import CliRunner

    from datamimic_ce.cli import app

    result = CliRunner().invoke(app, ["capabilities"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["_meta"]["format_version"] == 1
    assert data["_meta"]["view"] == "compact"
    assert "authoring_spec" not in data


def test_capabilities_cli_section_error_is_machine_readable() -> None:
    from typer.testing import CliRunner

    from datamimic_ce.cli import app

    result = CliRunner().invoke(app, ["capabilities", "--section", "bogus"])
    assert result.exit_code == 1
    data = json.loads(result.stdout)
    assert data["ok"] is False
    assert "bogus" in data["error"]
    assert isinstance(data["valid_sections"], list)


def test_capabilities_cli_section_and_full_are_mutually_exclusive() -> None:
    from typer.testing import CliRunner

    from datamimic_ce.cli import app

    result = CliRunner().invoke(app, ["capabilities", "--section", "x", "--full"])
    assert result.exit_code == 1


def test_capabilities_cli_section_mode_returns_keyed_dict() -> None:
    from typer.testing import CliRunner

    from datamimic_ce.cli import app

    result = CliRunner().invoke(app, ["capabilities", "--section", "rules"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert set(data) == {"rules"}
    assert isinstance(data["rules"], list)

    # Multiple sections
    result = CliRunner().invoke(app, ["capabilities", "--section", "elements,rules"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert set(data) == {"elements", "rules"}


def test_capabilities_cli_full_mode_is_unwrapped_manifest() -> None:
    from typer.testing import CliRunner

    from datamimic_ce.cli import app

    result = CliRunner().invoke(app, ["capabilities", "--full"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    # No _meta wrapper in full mode
    assert "_meta" not in data
    assert "authoring_spec" in data
    assert data["elements"]["generate"]["attributes"]  # full detail, not just names
