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
    # A version pin for a future EE-side CE-compat CI check to diff against.
    assert manifest["schema_version"], "capabilities_manifest() must carry a schema_version"
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
    # Constraints are present in manifest when element has them
    assert "constraints" in gen, "generate element must have constraints in manifest"
    assert len(gen["constraints"]) > 0, "generate element constraints must be non-empty"


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


def test_reference_element_surfaces_attribute_descriptions_untruncated() -> None:
    # Field(description=...) added to every CE model this session must actually reach the
    # agent-facing element_reference() text (it previously only reflected name/type/default),
    # and every element's reference must fit the clip budget without dropping attributes —
    # 'variable' (35 attrs) was the closest to overflow when this was added.
    index = build_schema_index()
    for tag in index.tags:
        text = reference("element", tag)
        assert "[truncated" not in text, f"<{tag}> reference overflowed the clip budget"
    text = reference("element", "generate")
    assert "Number of records to generate" in text  # GenerateModel.count's description


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


def test_constraint_three_surface_consistency_all_or_none() -> None:
    """Gate: GenerateModel's AllOrNone(start, end, interval) constraint appears
    identically in all three surfaces: (a) element_json_schema, (b) capabilities_manifest,
    (c) element_reference prose. The three attribute sets must be identical."""
    from datamimic_ce.authoring.reference import capabilities_manifest, element_reference
    from datamimic_ce.authoring.schema import element_json_schema

    # Surface (a): JSON schema via Pydantic's json_schema_extra
    json_schema = element_json_schema("generate")
    constraints_a = json_schema.get("constraints", [])
    all_or_none_a = next(
        (c for c in constraints_a if c.get("kind") == "all_or_none"), None
    )
    assert all_or_none_a is not None, "generate must have all_or_none constraint in json_schema"
    attrs_a = set(all_or_none_a["attrs"])

    # Surface (b): capabilities_manifest
    manifest = capabilities_manifest()
    gen_manifest = manifest["elements"]["generate"]
    constraints_b = gen_manifest.get("constraints", [])
    all_or_none_b = next(
        (c for c in constraints_b if c.get("kind") == "all_or_none"), None
    )
    assert all_or_none_b is not None, "generate must have all_or_none constraint in manifest"
    attrs_b = set(all_or_none_b["attrs"])

    # Surface (c): element_reference prose
    prose = element_reference("generate")
    # Find the line matching the all_or_none pattern: "<attrs>: all together or none"
    all_or_none_line = None
    for line in prose.splitlines():
        if "all together or none" in line:
            all_or_none_line = line
            break
    assert all_or_none_line is not None, (
        "generate reference must have 'all together or none' prose for AllOrNone constraint"
    )
    # Extract attrs from prose: "- <attr1>, <attr2>, <attr3>: all together or none"
    # Split on ": all together or none" to get the attr part, then split on ", "
    attrs_part = all_or_none_line.split(": all together or none")[0].strip("- ").strip()
    attrs_c = set(attrs_part.split(", "))

    # Assert all three surfaces have the same attribute set
    assert attrs_a == attrs_b == attrs_c, (
        f"AllOrNone attrs mismatch across surfaces: "
        f"json_schema={attrs_a}, manifest={attrs_b}, prose={attrs_c}"
    )


def test_reference_unique_constraints_reach_capabilities_and_reference() -> None:
    from datamimic_ce.authoring.reference import capabilities_manifest, element_reference

    constraints = capabilities_manifest()["elements"]["reference"]["constraints"]
    assert any(
        fact["kind"] == "forbids"
        and fact["attr"] == "unique"
        and fact["excludes"] == ["cyclic"]
        for fact in constraints
    )
    assert any(
        fact["kind"] == "allowed_values_when"
        and fact["when_attr"] == "unique"
        and fact["allowed"] == ["random"]
        for fact in constraints
    )

    prose = element_reference("reference")
    assert "unique cannot combine with: cyclic" in prose
    assert "distribution must be one of: random (when unique is true)" in prose
