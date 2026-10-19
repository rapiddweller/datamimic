"""CE verification guarantees survive the scaffold-to-Build migration."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
from datamimic_ce.authoring.adapters.validator import CeDescriptorValidator
from datamimic_ce.authoring.domain.build_rules import catalog_diagnostic
from datamimic_ce.authoring.domain.capture import (
    CapturedProduct,
    CapturedProducts,
    CaptureStatus,
    ProductCaptureEvidence,
    SmokeExportCapture,
)
from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId, DiagnosticPhase
from datamimic_ce.authoring.domain.proof import ReplayMismatchKind, VerificationGateStatus
from datamimic_ce.authoring.domain.requests import (
    BoundedExecutionEvidence,
    BuildRequestV4,
    LintResult,
    ReadyBuild,
    RejectedBuild,
)
from datamimic_ce.interfaces.cli import app


def _request(*, seed: int | None = 7, count: int = 2, exporter: bool = True, **options) -> BuildRequestV4:
    properties = {"name": "items", "count": count}
    if exporter:
        properties["target"] = "JSON"
    return BuildRequestV4.model_validate(
        {
            "document": {
                "root": {
                    "kind": "setup",
                    "properties": {"rng_seed": seed} if seed is not None else {},
                    "children": [
                        {
                            "kind": "generate",
                            "properties": properties,
                            "children": [
                                {"kind": "key", "properties": {"name": "id", "generator": "IncrementGenerator"}},
                            ],
                        },
                    ],
                }
            },
            **options,
        }
    )


def _captured(*, rows=({"id": 1}, {"id": 2}), ok=True, base_run_ok=True, smoke=None) -> BoundedExecutionEvidence:
    provenance = ProductCaptureEvidence(
        status=CaptureStatus.COMPLETE,
        requested=len(rows),
        observed=len(rows),
        limit=10,
        reason="Complete controlled executor-port capture",
    )
    return BoundedExecutionEvidence(
        ok=ok,
        base_run_ok=base_run_ok,
        captured=CapturedProducts((CapturedProduct("items", tuple(rows), provenance),), 10),
        smoke_export=smoke or SmokeExportCapture.not_requested(),
    )


@pytest.fixture
def executions(monkeypatch):
    original = CeBoundedExecutor.execute
    calls = []

    def recorded(executor, request):
        calls.append(request)
        return original(executor, request)

    monkeypatch.setattr(CeBoundedExecutor, "execute", recorded)
    return calls


def test_default_build_uses_one_real_capture_and_unrequested_gates(tmp_path: Path, executions) -> None:
    result = create_authoring_application(workspace_root=tmp_path).build(_request())
    assert isinstance(result, ReadyBuild), result
    assert len(executions) == 1
    assert result.verification.smoke_export.status is VerificationGateStatus.NOT_REQUESTED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.NOT_REQUESTED


def test_smoke_reuses_first_capture_and_real_json_exporter(tmp_path: Path, executions) -> None:
    result = create_authoring_application(workspace_root=tmp_path).build(_request(verification={"smoke_export": True}))
    assert isinstance(result, ReadyBuild), result
    assert [request.smoke_export for request in executions] == [True]
    smoke = result.verification.smoke_export
    assert smoke.status is VerificationGateStatus.PASSED
    assert (smoke.applicable_exporters, smoke.attempted_exporters, smoke.failed_exporters) == (1, 1, 0)
    assert not list(tmp_path.iterdir()), "Bounded smoke must not write project artifacts."


def test_requested_smoke_without_exporter_is_not_applicable(tmp_path: Path) -> None:
    result = create_authoring_application(workspace_root=tmp_path).build(
        _request(exporter=False, verification={"smoke_export": True})
    )
    assert isinstance(result, ReadyBuild), result
    assert result.verification.smoke_export.status is VerificationGateStatus.NOT_APPLICABLE
    assert result.verification.smoke_export.applicable_exporters == 0


def test_smoke_failure_cannot_be_masked_by_passing_acceptance(tmp_path: Path, monkeypatch) -> None:
    failed = _captured(ok=False, smoke=SmokeExportCapture(True, 1, 1, 1))
    monkeypatch.setattr(CeBoundedExecutor, "execute", lambda executor, request: failed)
    result = create_authoring_application(workspace_root=tmp_path).build(_request(verification={"smoke_export": True}))
    assert isinstance(result, RejectedBuild)
    assert result.phase is DiagnosticPhase.EVIDENCE
    assert result.verification.smoke_export.status is VerificationGateStatus.FAILED
    assert result.evidence[0].count == 2


@pytest.mark.parametrize("smoke_failed", [False, True], ids=["base_failure", "base_and_smoke_failure"])
def test_base_failure_preserves_exact_smoke_status_and_blocks_replay(tmp_path: Path, monkeypatch, smoke_failed) -> None:
    smoke = SmokeExportCapture(True, 1, 1, 1) if smoke_failed else SmokeExportCapture.not_requested()
    failed = _captured(ok=False, base_run_ok=False, smoke=smoke)
    calls = []

    def execute(executor, request):
        calls.append(request)
        return failed

    monkeypatch.setattr(CeBoundedExecutor, "execute", execute)
    result = create_authoring_application(workspace_root=tmp_path).build(
        _request(verification={"smoke_export": True, "deterministic_replay": True})
    )
    assert isinstance(result, RejectedBuild)
    assert len(calls) == 1
    expected = VerificationGateStatus.FAILED if smoke_failed else VerificationGateStatus.BLOCKED
    assert result.verification.smoke_export.status is expected
    assert result.verification.deterministic_replay.status is VerificationGateStatus.BLOCKED


def test_compile_failure_blocks_requested_gates_without_execution(tmp_path: Path, executions) -> None:
    request = BuildRequestV4.model_validate(
        {
            "document": {
                "root": {
                    "kind": "setup",
                    "children": [
                        {"kind": "unknown-element"},
                    ],
                }
            },
            "verification": {"smoke_export": True, "deterministic_replay": True},
        }
    )
    result = create_authoring_application(workspace_root=tmp_path).build(request)
    assert isinstance(result, RejectedBuild)
    assert result.phase is DiagnosticPhase.COMPILE
    assert executions == []
    assert result.verification.smoke_export.status is VerificationGateStatus.BLOCKED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.BLOCKED


def test_lint_failure_blocks_requested_gates_without_execution(tmp_path: Path, monkeypatch, executions) -> None:
    diagnostic = catalog_diagnostic(
        AuthoringRuleId.VALIDATION, "Controlled validation failure.", phase=DiagnosticPhase.XML
    )
    monkeypatch.setattr(
        CeDescriptorValidator,
        "validate",
        lambda validator, xml, **kwargs: LintResult(ok=False, diagnostics=(diagnostic,)),
    )
    result = create_authoring_application(workspace_root=tmp_path).build(
        _request(verification={"smoke_export": True, "deterministic_replay": True})
    )
    assert isinstance(result, RejectedBuild)
    assert result.phase is DiagnosticPhase.XML
    assert executions == []
    assert result.verification.smoke_export.status is VerificationGateStatus.BLOCKED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.BLOCKED


def test_replay_checks_complete_rows_beyond_response_samples(tmp_path: Path, monkeypatch) -> None:
    captures = iter((_captured(), _captured(rows=({"id": 1}, {"id": 99}))))
    calls = []

    def execute(executor, request):
        calls.append(request)
        return next(captures)

    monkeypatch.setattr(CeBoundedExecutor, "execute", execute)
    result = create_authoring_application(workspace_root=tmp_path).build(
        _request(sample_rows=1, verification={"deterministic_replay": True})
    )
    assert isinstance(result, RejectedBuild)
    assert len(result.evidence[0].rows) == 1
    assert len(calls) == 2
    replay = result.verification.deterministic_replay
    assert replay.status is VerificationGateStatus.FAILED
    assert (replay.compared_products, replay.compared_rows) == (1, 2)
    assert replay.mismatches[0].kind is ReplayMismatchKind.ROW_CONTENT
    assert replay.mismatches[0].first_difference == 1


def test_seeded_replay_runs_exactly_twice_and_passes(tmp_path: Path, executions) -> None:
    result = create_authoring_application(workspace_root=tmp_path).build(
        _request(sample_rows=1, verification={"deterministic_replay": True})
    )
    assert isinstance(result, ReadyBuild), result
    assert len(executions) == 2
    assert len(result.evidence[0].rows) == 1
    replay = result.verification.deterministic_replay
    assert replay.status is VerificationGateStatus.PASSED
    assert (replay.compared_products, replay.compared_rows) == (1, 2)


def test_unseeded_replay_fails_without_claiming_comparison(tmp_path: Path, executions) -> None:
    result = create_authoring_application(workspace_root=tmp_path).build(
        _request(seed=None, verification={"deterministic_replay": True})
    )
    assert isinstance(result, RejectedBuild)
    assert len(executions) == 1
    replay = result.verification.deterministic_replay
    assert replay.status is VerificationGateStatus.FAILED
    assert replay.compared_rows == 0
    assert "explicit" in replay.reason


def test_capped_acceptance_cannot_be_rescued_by_replay(tmp_path: Path, executions) -> None:
    result = create_authoring_application(workspace_root=tmp_path).build(
        _request(max_count=1, sample_rows=1, verification={"deterministic_replay": True})
    )
    assert isinstance(result, RejectedBuild)
    assert result.phase is DiagnosticPhase.EVIDENCE
    assert len(executions) == 1
    assert result.verification.deterministic_replay.status is VerificationGateStatus.BLOCKED
    assert 'count="2"' in result.review_artifact.compiled_xml


def test_cli_application_byte_parity_for_smoke_and_replay(tmp_path: Path) -> None:
    request = _request(sample_rows=1, verification={"smoke_export": True, "deterministic_replay": True})
    expected = create_authoring_application(workspace_root=tmp_path).build(request)
    assert isinstance(expected, ReadyBuild), expected
    result = CliRunner().invoke(
        app,
        ["authoring", "build", "-", "--workspace-root", str(tmp_path)],
        input=request.model_dump_json(exclude_none=True),
    )
    assert result.exit_code == 0, result.stdout
    assert result.stdout.strip() == expected.model_dump_json(indent=2)


def test_missing_memstore_identity_proof_blocks_gates_before_execution(tmp_path: Path, executions) -> None:
    payload = json.loads(_request(exporter=False).model_dump_json())
    root = payload["document"]["root"]
    root["children"][0]["properties"]["target"] = "store"
    root["children"].insert(0, {"kind": "memstore", "properties": {"id": "store"}})
    root["children"].append(
        {
            "kind": "generate",
            "properties": {
                "name": "readback",
                "source": "store",
                "type": "items",
                "distribution": "ordered",
            },
            "children": [{"kind": "key", "properties": {"name": "id", "script": "this.id"}}],
        }
    )
    payload["verification"] = {"smoke_export": True, "deterministic_replay": True}
    result = create_authoring_application(workspace_root=tmp_path).build(BuildRequestV4.model_validate(payload))
    assert isinstance(result, RejectedBuild)
    assert result.phase is DiagnosticPhase.EXPECTATION
    assert executions == []
    assert result.verification.smoke_export.status is VerificationGateStatus.BLOCKED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.BLOCKED


@pytest.mark.parametrize("traversal_count", ["{1}", "{1/0}"])
def test_dynamic_file_count_never_gets_exhaustion_proof(tmp_path: Path, traversal_count: str) -> None:
    from datamimic_ce.authoring.adapters.dm_json_codec import CeDmJsonCodec

    (tmp_path / "rows.csv").write_text("id\n1\n2\n3\n", encoding="utf-8")
    xml = (
        '<setup rngSeed="7"><generate name="rows" source="rows.csv" distribution="ordered" '
        f'count="{traversal_count}" target="JSON"><key name="id" script="this.id"/></generate></setup>'
    )
    request = BuildRequestV4.model_validate(
        {
            "document": CeDmJsonCodec().decompile(xml),
            "expectations": [{"kind": "exact_count", "subject": {"kind": "product", "product": "rows"}, "count": 3}],
            "verification": {"smoke_export": True, "deterministic_replay": True},
        }
    )
    result = create_authoring_application(workspace_root=tmp_path).build(request)
    assert isinstance(result, RejectedBuild), result
    assert result.phase is DiagnosticPhase.EVIDENCE
    assert result.evidence[0].capture.status is CaptureStatus.UNKNOWN
    assert result.evidence[0].capture.requested is None
    assert not result.evidence[0].capture.complete
    assert result.verification.deterministic_replay.status is VerificationGateStatus.BLOCKED
    assert f'count="{traversal_count}"' in result.review_artifact.compiled_xml


@pytest.mark.parametrize("traversal_count", [1, 3])
def test_literal_file_count_agrees_with_unmodified_runtime(tmp_path: Path, traversal_count: int) -> None:
    from datamimic_ce.authoring.adapters.dm_json_codec import CeDmJsonCodec
    from datamimic_ce.engine.runtime.api import create_run_session
    from datamimic_ce.engine.runtime.contracts import RunRequest as RuntimeRequest

    (tmp_path / "rows.csv").write_text("id\n1\n2\n3\n", encoding="utf-8")
    xml = (
        '<setup rngSeed="7"><generate name="rows" source="rows.csv" distribution="ordered" '
        f'count="{traversal_count}" target="JSON"><key name="id" script="this.id"/></generate></setup>'
    )
    request = BuildRequestV4.model_validate(
        {
            "document": CeDmJsonCodec().decompile(xml),
            "expectations": [
                {"kind": "exact_count", "subject": {"kind": "product", "product": "rows"}, "count": traversal_count}
            ],
            "verification": {"smoke_export": True, "deterministic_replay": True},
        }
    )
    result = create_authoring_application(workspace_root=tmp_path).build(request)
    assert isinstance(result, ReadyBuild), result
    descriptor = tmp_path / "model.xml"
    descriptor.write_text(result.artifact.compiled_xml, encoding="utf-8")
    captured = create_run_session(RuntimeRequest(descriptor_path=descriptor, test_mode=True)).execute().captured
    assert len(captured["rows"]) == result.evidence[0].count == traversal_count
    assert result.verification.smoke_export.status is VerificationGateStatus.PASSED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.PASSED


@pytest.mark.parametrize("nested", [False, True], ids=["scalar", "nested"])
@pytest.mark.parametrize("native_type", ["string", "decimal"])
def test_fixed_value_keeps_native_types_at_every_depth(tmp_path: Path, nested: bool, native_type: str) -> None:
    from datamimic_ce.authoring.adapters.dm_json_codec import CeDmJsonCodec

    field = f'<key name="payload" type="{native_type}" constant="1.2"/>'
    expected: str | dict[str, str] = "1.2"
    if nested:
        field = (
            '<nestedKey name="payload" type="dict">'
            f'<key name="amount" type="{native_type}" constant="1.2"/></nestedKey>'
        )
        expected = {"amount": "1.2"}
    xml = f'<setup rngSeed="7"><generate name="rows" count="1">{field}</generate></setup>'
    request = BuildRequestV4.model_validate(
        {
            "document": CeDmJsonCodec().decompile(xml),
            "expectations": [
                {
                    "kind": "fixed_value",
                    "subject": {"kind": "product", "product": "rows"},
                    "field": "payload",
                    "value": expected,
                }
            ],
        }
    )
    result = create_authoring_application(workspace_root=tmp_path).build(request)
    assert isinstance(result, ReadyBuild if native_type == "string" else RejectedBuild), result
    if native_type == "decimal":
        assert any(item.code == "fixed_value" for item in result.diagnostics)


@pytest.mark.parametrize(
    "producer_properties,entity",
    [
        ({}, "items"),
        ({"type": "shared"}, "shared"),
        ({"target_entity": "shared"}, "shared"),
        ({"type": "ignored", "target_entity": "shared"}, "shared"),
    ],
)
def test_memstore_readback_uses_resolved_output_entity(
    tmp_path: Path, producer_properties: dict[str, str], entity: str
) -> None:
    payload = json.loads(_request(exporter=False).model_dump_json())
    children = payload["document"]["root"]["children"]
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
    payload["product_roles"] = [
        {"product": "items", "field": "id", "role": {"kind": "identifier"}},
        {
            "product": "copy",
            "field": "id",
            "role": {"kind": "foreign_key", "parent_product": "items", "parent_field": "id"},
        },
    ]
    payload["verification"] = {"smoke_export": True, "deterministic_replay": True}
    result = create_authoring_application(workspace_root=tmp_path).build(BuildRequestV4.model_validate(payload))
    assert isinstance(result, ReadyBuild), result
    by_name = {item.name: item for item in result.evidence}
    assert by_name["items"].rows == by_name["copy"].rows == ({"id": 1}, {"id": 2})
    assert all(item.capture.complete for item in result.evidence)
    assert result.verification.smoke_export.status is VerificationGateStatus.PASSED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.PASSED


def test_conditional_field_union_matches_unmodified_runtime(tmp_path: Path) -> None:
    from datamimic_ce.authoring.adapters.dm_json_codec import CeDmJsonCodec
    from datamimic_ce.engine.runtime.api import create_run_session
    from datamimic_ce.engine.runtime.contracts import RunRequest as RuntimeRequest

    xml = (
        '<setup rngSeed="7"><generate name="rows" count="3" target="JSON">'
        '<key name="id" generator="IncrementGenerator"/>'
        '<condition><if condition="this.id == 1"><key name="code" constant="a"/></if>'
        '<else-if condition="this.id == 2"><key name="code" constant="b"/></else-if>'
        '<else><key name="code" constant="c"/></else></condition></generate></setup>'
    )
    request = BuildRequestV4.model_validate(
        {
            "document": CeDmJsonCodec().decompile(xml),
            "expectations": [
                {
                    "kind": "allowed_values",
                    "subject": {"kind": "product", "product": "rows"},
                    "field": "code",
                    "values": ["a", "b", "c"],
                }
            ],
            "verification": {"smoke_export": True, "deterministic_replay": True},
        }
    )
    result = create_authoring_application(workspace_root=tmp_path).build(request)
    assert isinstance(result, ReadyBuild), result
    descriptor = tmp_path / "model.xml"
    descriptor.write_text(xml, encoding="utf-8")
    captured = create_run_session(RuntimeRequest(descriptor_path=descriptor, test_mode=True)).execute().captured
    expected = ({"id": 1, "code": "a"}, {"id": 2, "code": "b"}, {"id": 3, "code": "c"})
    assert tuple(captured["rows"]) == result.evidence[0].rows == expected
    assert result.verification.smoke_export.status is VerificationGateStatus.PASSED
    assert result.verification.deterministic_replay.status is VerificationGateStatus.PASSED
