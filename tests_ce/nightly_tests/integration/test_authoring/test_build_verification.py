# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Build gates that need an unmodified runtime, exporter, replay, or file scan."""

from pathlib import Path

import pytest

from datamimic_ce.authoring.domain.dm_json import DmJsonDocumentV1
from datamimic_ce.authoring.domain.proof import VerificationGateStatus
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, ReadyBuild, RejectedBuild
from tests_ce.authoring_project import build_document, build_project, entry_digest


@pytest.mark.integration
@pytest.mark.parametrize("traversal_count", [1, 3])
def test_literal_file_count_agrees_with_unmodified_runtime(tmp_path: Path, traversal_count: int) -> None:
    from datamimic_ce.engine.runtime.api import create_run_session
    from datamimic_ce.engine.runtime.contracts import RunRequest as RuntimeRequest

    (tmp_path / "rows.csv").write_text("id\n1\n2\n3\n", encoding="utf-8")
    xml = (
        '<setup rngSeed="7"><generate name="rows" source="rows.csv" distribution="ordered" '
        f'count="{traversal_count}" target="JSON"><key name="id" script="this.id"/></generate></setup>'
    )
    result = build_project(
        tmp_path,
        xml,
        expectations=[
            {"kind": "exact_count", "subject": {"kind": "product", "product": "rows"}, "count": traversal_count}
        ],
        verification={"smoke_export": True, "deterministic_replay": True},
    )
    assert isinstance(result, ReadyBuild), result
    # Run the very entry bytes the artifact binds.
    assert {item.path: item.sha256 for item in result.artifact.files}[PROJECT_ENTRY_PATH] == entry_digest(tmp_path)
    descriptor = tmp_path / PROJECT_ENTRY_PATH
    captured = create_run_session(RuntimeRequest(descriptor_path=descriptor, test_mode=True)).execute().captured
    assert len(captured["rows"]) == result.evidence[0].count == traversal_count
    assert result.verification.smoke_export.status is VerificationGateStatus.PASSED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.PASSED


@pytest.mark.integration
@pytest.mark.parametrize("nested", [False, True], ids=["scalar", "nested"])
@pytest.mark.parametrize("native_type", ["string", "decimal"])
def test_fixed_value_keeps_native_types_at_every_depth(tmp_path: Path, nested: bool, native_type: str) -> None:
    field = f'<key name="payload" type="{native_type}" constant="1.2"/>'
    expected: str | dict[str, str] = "1.2"
    if nested:
        field = (
            '<nestedKey name="payload" type="dict">'
            f'<key name="amount" type="{native_type}" constant="1.2"/></nestedKey>'
        )
        expected = {"amount": "1.2"}
    xml = f'<setup rngSeed="7"><generate name="rows" count="1">{field}</generate></setup>'
    result = build_project(
        tmp_path,
        xml,
        expectations=[
            {
                "kind": "fixed_value",
                "subject": {"kind": "product", "product": "rows"},
                "field": "payload",
                "value": expected,
            }
        ],
    )
    assert isinstance(result, ReadyBuild if native_type == "string" else RejectedBuild), result
    if native_type == "decimal":
        assert any(item.code == "fixed_value" for item in result.diagnostics)


@pytest.mark.integration
@pytest.mark.parametrize(
    "producer_properties,entity",
    [
        ({}, "items"),
        ({"type": "ignored"}, "items"),  # type names only a memstore read (#422)
        ({"target_entity": "shared"}, "shared"),
        ({"type": "ignored", "target_entity": "shared"}, "shared"),
    ],
)
def test_memstore_readback_uses_resolved_output_entity(
    tmp_path: Path, producer_properties: dict[str, str], entity: str
) -> None:
    document = build_document(exporter=False).model_dump(mode="json")
    children = document["root"]["children"]
    children[0]["properties"].update(target="store", **producer_properties)
    children.insert(0, {"kind": "memstore", "properties": {"id": "store"}})
    children.append(
        {
            "kind": "generate",
            "properties": {
                "name": "copy",
                "source": "store",
                "source_entity": entity,
                "distribution": "ordered",
                "target": "JSON",
            },
            "children": [{"kind": "key", "properties": {"name": "id", "script": "this.id"}}],
        }
    )
    product_roles = [
        {"product": "items", "field": "id", "role": {"kind": "identifier"}},
        {
            "product": "copy",
            "field": "id",
            "role": {"kind": "foreign_key", "parent_product": "items", "parent_field": "id"},
        },
    ]
    result = build_project(
        tmp_path,
        DmJsonDocumentV1.model_validate(document),
        product_roles=product_roles,
        verification={"smoke_export": True, "deterministic_replay": True},
    )
    assert isinstance(result, ReadyBuild), result
    by_name = {item.name: item for item in result.evidence}
    assert by_name["items"].rows == by_name["copy"].rows == ({"id": 1}, {"id": 2})
    assert all(item.capture.complete for item in result.evidence)
    assert result.verification.smoke_export.status is VerificationGateStatus.PASSED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.PASSED


@pytest.mark.integration
def test_conditional_field_union_matches_unmodified_runtime(tmp_path: Path) -> None:
    from datamimic_ce.engine.runtime.api import create_run_session
    from datamimic_ce.engine.runtime.contracts import RunRequest as RuntimeRequest

    xml = (
        '<setup rngSeed="7"><generate name="rows" count="3" target="JSON">'
        '<key name="id" generator="IncrementGenerator"/>'
        '<condition><if condition="this.id == 1"><key name="code" constant="a"/></if>'
        '<else-if condition="this.id == 2"><key name="code" constant="b"/></else-if>'
        '<else><key name="code" constant="c"/></else></condition></generate></setup>'
    )
    result = build_project(
        tmp_path,
        xml,
        expectations=[
            {
                "kind": "allowed_values",
                "subject": {"kind": "product", "product": "rows"},
                "field": "code",
                "values": ["a", "b", "c"],
            }
        ],
        verification={"smoke_export": True, "deterministic_replay": True},
    )
    assert isinstance(result, ReadyBuild), result
    descriptor = tmp_path / PROJECT_ENTRY_PATH
    captured = create_run_session(RuntimeRequest(descriptor_path=descriptor, test_mode=True)).execute().captured
    expected = ({"id": 1, "code": "a"}, {"id": 2, "code": "b"}, {"id": 3, "code": "c"})
    assert tuple(captured["rows"]) == result.evidence[0].rows == expected
    assert result.verification.smoke_export.status is VerificationGateStatus.PASSED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.PASSED
