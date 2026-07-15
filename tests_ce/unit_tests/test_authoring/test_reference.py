# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.

"""Reference projections remain derived from canonical registries and models."""

import pytest

from datamimic_ce.authoring.reference import ReferenceTopic, capabilities_manifest, reference
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
