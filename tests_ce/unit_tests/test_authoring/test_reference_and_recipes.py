# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Reference/cheatsheet/recipes: derived content, packaging, EE-leak gate,
and the recipes-cannot-rot CI (lint clean + dry-run the runnable ones)."""

import re
from importlib import resources

import pytest

from datamimic_ce.authoring import lint_source
from datamimic_ce.authoring.dryrun import dry_run_source
from datamimic_ce.authoring.reference import (
    _recipes_index,
    cheatsheet,
    known_generator_names,
    load_recipe,
    reference,
)
from datamimic_ce.authoring.schema import ALIASES, ELEMENT_MODEL_MAP, build_schema_index

# Gate 3: EE-only concepts must never leak into agent-facing content (CE has no
# kafka/object-storage/dwh; 'bucket' was purged dead EE surface).
_EE_TERMS = re.compile(
    r"kafka|minio|\bs3\b|object.storage|\bdwh\b|bucket|targetClient|storageId|sourceUri|mpPlatform",
    re.IGNORECASE,
)


def _recipe_xml(recipe_id: str) -> str:
    return (resources.files("datamimic_ce.authoring") / "recipes" / f"{recipe_id}.xml").read_text(
        encoding="utf-8"
    )


def _recipe_ids() -> list[str]:
    return [entry["id"] for entry in _recipes_index()["recipe"]]


def test_cheatsheet_packaged_and_capped() -> None:
    text = cheatsheet()
    assert "<setup" in text and len(text) < 16000


def test_gate3_no_ee_terms_in_agent_content() -> None:
    corpus = "".join(
        reference(t) for t in ("overview", "targets", "distributions", "context", "timeseries", "recipes")
    )
    for recipe_id in _recipe_ids():
        corpus += _recipe_xml(recipe_id)
    assert not _EE_TERMS.search(corpus), _EE_TERMS.search(corpus)


def test_reference_timeseries_documents_ts_namespace() -> None:
    text = reference("timeseries")
    for token in ("ts.now", "ts.step", "ts.series", "interval", "series"):
        assert token in text


def test_reference_distributions_documents_numeric_sequences() -> None:
    from datamimic_ce.enums.distribution_enums import NumberDistribution

    text = reference("distributions")
    for member in NumberDistribution:
        assert member.value in text
    assert "multiprocessing" in text
    assert "finite positional sequences" in text


def test_cheatsheet_documents_numeric_sequence_distributions() -> None:
    text = cheatsheet()
    for token in ("step", "shuffle", "wedge", "bitreverse", "fibonacci", "padovan", "randomWalk"):
        assert token in text
    assert "worker-local iterator" in text


def test_reference_converters_derived_from_enum() -> None:
    from datamimic_ce.enums.converter_enums import ConverterEnum

    text = reference("converters")
    for member in ConverterEnum:
        assert member.value in text  # SPOT: every engine converter is documented
    assert "Converter" in text and "execute" in text  # the custom-extension seam


def test_capabilities_manifest_matches_registries() -> None:
    from datamimic_ce.authoring.reference import capabilities_manifest
    from datamimic_ce.enums.converter_enums import ConverterEnum
    from datamimic_ce.enums.distribution_enums import NumberDistribution, SourceDistribution
    from datamimic_ce.exporters.exporter_util import _BUFFERED_EXPORTERS

    manifest = capabilities_manifest()
    # SPOT: every section mirrors its live registry, nothing invented
    assert set(manifest["elements"]) == build_schema_index().tags
    assert manifest["aliases"] == ALIASES
    assert set(manifest["converters"]) == {m.value for m in ConverterEnum}
    assert set(manifest["targets"]["file_exporters"]) == set(_BUFFERED_EXPORTERS)
    assert set(manifest["distributions"]) == {m.value for m in SourceDistribution}
    assert set(manifest["numeric_distributions"]) == {m.value for m in NumberDistribution}
    assert "IncrementGenerator" in manifest["generators"]
    assert "Person" in manifest["entities"]
    gen = manifest["elements"]["generate"]
    assert gen["attributes"]["name"]["required"] is True
    assert "key" in gen["children"]


def test_gate3_cheatsheet_elements_exist_in_schema() -> None:
    index = build_schema_index()
    known = index.tags | {"comment"}
    for tag in re.findall(r"<(\w[\w-]*)[ >/=]?", cheatsheet()):
        if tag in ("setup",):  # root included in known anyway
            continue
        assert tag in known or tag in ALIASES, f"cheatsheet mentions unknown element <{tag}>"


def test_reference_element_topic_lists_attributes() -> None:
    text = reference("element", "generate")
    assert "pageSize" in text and "(required)" in text and "Aliases: <iterate>" in text


def test_reference_element_unknown_lists_valid() -> None:
    with pytest.raises(ValueError, match="Unknown element"):
        reference("element", "generat")


def test_reference_generators_derived_and_reserved_names_covered() -> None:
    names = known_generator_names()
    assert {"IncrementGenerator", "DateTimeGenerator", "BooleanGenerator"} <= names
    assert "IncrementGenerator" in reference("generators", "increment")


def test_reference_targets_from_registry() -> None:
    text = reference("targets")
    for target in ("CSV", "JSON", "DbUnit", "ConsoleExporter"):
        assert target in text


def test_reference_entities_enumerated_from_registry() -> None:
    from datamimic_ce.domains.domain_core.entity_registry import list_entity_specs

    listing = reference("entities")
    for entity in (s.entity for s in list_entity_specs()):
        assert entity in listing
    person = reference("entities", "Person")
    assert "given_name" in person and "email" in person
    with pytest.raises(ValueError, match="Unknown entity"):
        reference("entities", "NotAnEntity")


def test_reference_context_documents_scope_aliases() -> None:
    text = reference("context").lower()
    for token in ("this.", "parent.", "root.", "bare name"):
        assert token in text


def test_every_recipe_lints_clean() -> None:
    for recipe_id in _recipe_ids():
        result = lint_source(_recipe_xml(recipe_id))
        errors = [d for d in result.diagnostics if d.severity.value == "error"]
        assert not errors, f"{recipe_id}: {[d.message for d in errors]}"


@pytest.mark.parametrize("recipe_id", [e["id"] for e in _recipes_index()["recipe"] if e["runnable"]])
def test_runnable_recipes_dry_run(recipe_id: str) -> None:
    result = dry_run_source(_recipe_xml(recipe_id), max_count=5, sample_rows=2)
    assert result.ok, [d.message for d in result.diagnostics]
    assert result.products and all(p.count > 0 for p in result.products)


def test_recipe_loader_and_unknown() -> None:
    assert "```xml" in load_recipe("csv-to-json-pipeline")
    with pytest.raises(ValueError, match="Unknown recipe"):
        load_recipe("no-such-recipe")


def test_element_model_map_covers_all_element_constants() -> None:
    from datamimic_ce.constants import element_constants

    declared = {
        value
        for name, value in vars(element_constants).items()
        if name.startswith("EL_") and isinstance(value, str)
    }
    assert declared - {"comment"} == set(ELEMENT_MODEL_MAP), "element constant not covered by the map"
