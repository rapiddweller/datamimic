# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Executable CE authoring-rule provenance and scope matrix.

This is a coverage ledger, not another runtime policy owner.  Every positive row
asserts facts projected from the central CE model/element registries.  Negative
rows keep EE-only vocabulary out of CE authoring so CLI/MCP cannot recommend a
feature that this runtime does not implement.

Provenance and exact CE scope:

* ADR-006: covered for ``count={expr}`` and the count/source/script fallback.
  EE setup-attribute semantics for object-storage attributes and ``{{expr}}``
  diagnostics are not claimed here.
* ADR-029: covered for optional-header ``.wgt.csv`` key sources and the rule that
  key-source weighting cannot combine with ``unique``.  EE's newer strict
  two-column/finite/non-negative/positive-sum parser contract is not claimed.
* ADR-041: covered at the authoring boundary for condition/default metadata and
  accepted stable shapes.  This gate does not pin EE 3.5 runtime error quirks.
* ADR-042 + its DSL matrix: covered for CE's two distinct distribution domains,
  their exact vocabularies, and unique precedence.  EE-only full-pool source
  distributions, I900, and Phase 2-4 MP classifiers are excluded.
* Kafka, object storage, and an ``<operate>`` element are excluded. Other
  skill-catalog tags absent from the live CE registry are excluded as well; they
  are not inferred into CE merely because the EE DSL skill documents them. CE database
  operations remain target strings (``client.update/upsert/delete``), not an
  ``<operate>`` element. ``exportUri`` remains valid for CE file exporters and is
  intentionally not part of the object-storage exclusion.
"""

from pathlib import Path

import pytest

from datamimic_ce.authoring.reference import capabilities_manifest
from datamimic_ce.enums.distribution_enums import NumberDistribution, SourceDistribution
from datamimic_ce.model.constraints import element_constraints, serialize_constraints
from datamimic_ce.model.generate_model import GenerateModel
from datamimic_ce.model.nested_key_model import NestedKeyModel
from datamimic_ce.utils.file_util import FileUtil

CE_SOURCE_DISTRIBUTIONS = frozenset({"random", "ordered", "cumulated"})
EE_ONLY_SOURCE_DISTRIBUTIONS = frozenset({"round_robin", "reservoir", "weighted", "stratified"})
EE_ONLY_ELEMENTS = frozenset(
    {
        "ama-generate",
        "kafka",
        "mapping",
        "ml-train",
        "object-storage",
        "objectStorage",
        "operate",
        "param",
        "property",
        "rule",
        "sourceConstraints",
        "targetConstraints",
    }
)
EE_ONLY_ATTRIBUTES = frozenset({"sourceUri", "storageId", "stratifyBy", "targetClient"})


# (provenance, tag, partial serialized fact).  Partial facts deliberately ignore
# wording so message improvements do not weaken the semantic contract.
RULE_FACT_MATRIX = (
    (
        "ADR-006/count fallback",
        "generate",
        {
            "kind": "required_one_of",
            "attrs": ["count", "maxCount", "minCount", "script", "source"],
        },
    ),
    (
        "DSL/source companion",
        "generate",
        {"kind": "requires", "attr": "selector", "needs": ["source"]},
    ),
    (
        "DSL/source companion",
        "variable",
        {"kind": "requires", "attr": "separator", "needs": ["source"]},
    ),
    (
        "ADR-042/source unique precedence",
        "generate",
        {
            "kind": "allowed_values_when",
            "attr": "distribution",
            "allowed": ["random"],
            "when_attr": "unique",
            "when_true": True,
        },
    ),
    (
        "ADR-042/source unique precedence",
        "variable",
        {"kind": "forbids", "attr": "unique", "excludes": ["cyclic"]},
    ),
    (
        "ADR-042/reference unique precedence",
        "reference",
        {
            "kind": "allowed_values_when",
            "attr": "distribution",
            "allowed": ["random"],
            "when_attr": "unique",
            "when_true": True,
        },
    ),
    (
        "ADR-029/key weighted-source unique",
        "key",
        {"kind": "requires", "attr": "unique", "needs": ["values"], "when_true": True},
    ),
    (
        "ADR-042/key distribution domain",
        "key",
        {"kind": "requires", "attr": "distribution", "needs": ["type"]},
    ),
    (
        "ADR-042/key unique precedence",
        "key",
        {"kind": "forbids", "attr": "unique", "excludes": ["distribution"]},
    ),
    (
        "DSL/nested cyclic exit",
        "nestedKey",
        {"kind": "requires", "attr": "cyclic", "needs": ["script", "source"]},
    ),
    (
        "DSL/nested cyclic bound",
        "nestedKey",
        {
            "kind": "requires",
            "attr": "cyclic",
            "needs": ["count", "maxCount", "minCount"],
        },
    ),
)


def _contains_partial_fact(tag: str, expected: dict[str, object]) -> bool:
    facts = serialize_constraints(element_constraints(tag))
    return any(all(fact.get(key) == value for key, value in expected.items()) for fact in facts)


@pytest.mark.parametrize(("provenance", "tag", "expected"), RULE_FACT_MATRIX)
def test_rule_fact_matrix_is_owned_by_the_central_registry(
    provenance: str, tag: str, expected: dict[str, object]
) -> None:
    assert _contains_partial_fact(tag, expected), f"missing {provenance} fact on <{tag}>: {expected}"


def test_distribution_domains_and_ee_only_exclusions_are_exact() -> None:
    manifest = capabilities_manifest()

    source_values = frozenset(manifest["distributions"])
    number_values = frozenset(manifest["numeric_distributions"])

    assert source_values == CE_SOURCE_DISTRIBUTIONS
    assert source_values == frozenset(member.value for member in SourceDistribution)
    assert source_values.isdisjoint(EE_ONLY_SOURCE_DISTRIBUTIONS)
    assert number_values == frozenset(member.value for member in NumberDistribution)


def test_legacy_weight_column_metadata_does_not_claim_ee_weighted_distribution() -> None:
    description = capabilities_manifest()["elements"]["variable"]["attributes"]["weightColumn"]["description"]

    assert ".wgt.ent.csv" in description
    assert "not a distribution='weighted'" in description


def test_ee_only_elements_and_attributes_do_not_leak_into_cli_mcp_capabilities() -> None:
    elements = capabilities_manifest()["elements"]
    exposed_attributes = {attribute for element in elements.values() for attribute in element["attributes"]}

    assert set(elements).isdisjoint(EE_ONLY_ELEMENTS)
    assert exposed_attributes.isdisjoint(EE_ONLY_ATTRIBUTES)
    assert "exportUri" in elements["generate"]["attributes"]


def test_ce_file_memstore_database_and_mongodb_source_families_are_discoverable() -> None:
    elements = capabilities_manifest()["elements"]
    source_description = elements["generate"]["attributes"]["source"]["description"]

    assert {"memstore", "database", "mongodb"} <= set(elements)
    for token in ("file path", "<memstore>", "<database>", "<mongodb>"):
        assert token in source_description


def test_adr006_computed_count_is_accepted_and_described_from_the_model() -> None:
    model = GenerateModel(name="orders", count="{customers * orders_per_customer}")
    count_metadata = capabilities_manifest()["elements"]["generate"]["attributes"]["count"]

    assert model.count == "{customers * orders_per_customer}"
    assert "{script}" in count_metadata["description"]


@pytest.mark.parametrize(
    "attributes",
    (
        {"name": "omitted", "type": "dict", "condition": "False"},
        {"name": "fallback", "type": "dict", "condition": "False", "defaultValue": "{}"},
        {"name": "scripted", "script": "{'a': 1}"},
    ),
)
def test_adr041_stable_authoring_shapes_are_accepted(attributes: dict[str, object]) -> None:
    NestedKeyModel(**attributes)


def test_adr041_condition_and_default_semantics_reach_capabilities() -> None:
    attributes = capabilities_manifest()["elements"]["nestedKey"]["attributes"]

    assert "evaluates false" in attributes["condition"]["description"]
    assert "Fallback" in attributes["defaultValue"]["description"]


def test_adr029_ce_optional_header_subset(tmp_path: Path) -> None:
    headered = tmp_path / "headered.wgt.csv"
    headerless = tmp_path / "headerless.wgt.csv"
    headered.write_text("Equivalence class|Weighting factor\nA|3\nB|1\n", encoding="utf-8")
    headerless.write_text("A|3\nB|1\n", encoding="utf-8")

    with_header = FileUtil.read_weight_csv(headered, "|")
    without_header = FileUtil.read_weight_csv(headerless, "|")

    assert with_header[0].tolist() == without_header[0].tolist() == ["A", "B"]
    assert with_header[1].tolist() == without_header[1].tolist() == [0.75, 0.25]


def test_adr029_weighted_key_source_is_discoverable_but_not_overclaimed() -> None:
    source = capabilities_manifest()["elements"]["key"]["attributes"]["source"]

    assert "wgt.csv" in source["description"]
    assert "with replacement" in source["description"]
