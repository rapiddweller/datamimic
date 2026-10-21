"""Build preserves proof requests and rejects dishonest transport values."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.requests import PROJECT_ACCEPTANCE_PATH, PROJECT_ENTRY_PATH
from tests_ce.authoring_project import write_project


def _document() -> dict:
    return {"version": "1", "root": {"kind": "setup", "properties": {"rngSeed": 7}, "children": []}}


def _build_with_acceptance(root: Path, acceptance: str):
    """Build a trivial entry against raw acceptance/build.json text, the transport an agent writes."""
    write_project(root, '<setup rngSeed="7"/>')
    (root / PROJECT_ACCEPTANCE_PATH).write_text(acceptance, encoding="utf-8")
    return create_authoring_application(root, descriptor_path=PROJECT_ENTRY_PATH).build()


def test_build_uses_transaction_expectations_and_ce_verification() -> None:
    from datamimic_ce.authoring.domain.requests import BuildRequestV5

    request = BuildRequestV5.model_validate(
        {
            "expectations": [{"kind": "exact_count", "subject": {"kind": "product", "product": "cities"}, "count": 3}],
            "verification": {"smoke_export": True, "deterministic_replay": True},
        }
    )
    assert request.version == "5.0"
    assert request.expectations[0].count == 3
    assert request.verification.smoke_export is True
    assert request.verification.deterministic_replay is True


def test_build_rejects_duplicate_expectations(tmp_path: Path) -> None:
    from datamimic_ce.authoring.domain.diagnostics import DiagnosticPhase
    from datamimic_ce.authoring.domain.requests import RejectedBuild

    expectation = {"kind": "exact_count", "subject": {"kind": "product", "product": "cities"}, "count": 3}
    result = _build_with_acceptance(tmp_path, json.dumps({"expectations": [expectation, expectation]}))
    assert isinstance(result, RejectedBuild), result
    assert result.phase is DiagnosticPhase.MODEL
    assert "unique" in result.diagnostics[0].message


def test_role_and_caller_origin_survive_transport() -> None:
    from datamimic_ce.authoring.domain.requests import BuildRequestV5

    request = BuildRequestV5.model_validate(
        {
            "product_roles": [{"product": "cities", "field": "id", "role": {"kind": "identifier"}}],
            "acceptance_requirements": [
                {
                    "origin": "caller",
                    "expectation": {
                        "kind": "exact_count",
                        "subject": {"kind": "product", "product": "cities"},
                        "count": 3,
                    },
                }
            ],
        }
    )
    payload = request.model_dump(mode="json")
    assert payload["product_roles"][0]["role"] == {"kind": "identifier"}
    assert payload["acceptance_requirements"][0]["origin"] == "caller"


@pytest.mark.parametrize("count", [-1, True, "3"])
def test_product_evidence_rejects_untrusted_counts(count: object) -> None:
    from datamimic_ce.authoring.domain.requests import ProductEvidence

    with pytest.raises(ValidationError):
        ProductEvidence.model_validate({"name": "cities", "count": count, "rows": []})


def test_sample_length_is_not_total_count() -> None:
    from datamimic_ce.authoring.domain.requests import ProductEvidence

    evidence = ProductEvidence.model_validate({"name": "cities", "count": 100, "rows": [{"id": 1}]})
    assert evidence.count == 100
    assert len(evidence.rows) == 1


def test_list_and_per_parent_expectations_remain_distinct() -> None:
    from datamimic_ce.authoring.domain.requests import BuildRequestV5

    request = BuildRequestV5.model_validate(
        {
            "expectations": [
                {
                    "kind": "unique",
                    "subject": {"kind": "product", "product": "cities", "list_field": "districts"},
                    "field": "name",
                    "scope": "per_parent",
                },
                {
                    "kind": "per_parent_count",
                    "subject": {"kind": "per_parent", "parent_product": "cities", "child_product": "addresses"},
                    "count": 2,
                },
            ],
        }
    )
    assert request.expectations[0].subject.list_field == "districts"
    assert request.expectations[0].scope == "per_parent"
    assert request.expectations[1].subject.child_product == "addresses"


def test_ready_build_cannot_erase_a_failed_verification_gate() -> None:
    from datamimic_ce.authoring.domain.requests import ReadyBuild

    with pytest.raises(ValidationError, match="verification"):
        ReadyBuild.model_validate(
            {
                "artifact": {
                    "files": [
                        {"path": "acceptance/build.json", "sha256": "0" * 64},
                        {"path": "datamimic.xml", "sha256": "0" * 64},
                    ],
                    "ce_version": "5.0.0",
                },
                "assurance": {"mode": "local_bounded"},
                "evidence": [{"name": "cities", "count": 1, "rows": [{"id": 1}]}],
                "verification": {"smoke_export": {"status": "failed", "reason": "corrupt finalized file"}},
            }
        )


def test_input_error_has_an_actionable_typed_diagnostic() -> None:
    from datamimic_ce.authoring.domain.requests import RejectedBuild

    rejection = RejectedBuild.from_input_error("A Build document is required")
    assert rejection.outcome == "rejected"
    assert rejection.phase.value == "model"
    assert rejection.diagnostics[0].code.value == "input"
    assert rejection.diagnostics[0].remediation


def test_validation_diagnostics_omit_input_secrets_and_none_prefix(tmp_path: Path) -> None:
    from datamimic_ce.authoring.domain.requests import RejectedBuild

    rejection = _build_with_acceptance(tmp_path, json.dumps({"version": "a-private-token"}))
    assert isinstance(rejection, RejectedBuild), "wrong protocol version was accepted"
    assert rejection.diagnostics[0].path == ("version",)
    assert "a-private-token" not in rejection.model_dump_json()
    assert not rejection.diagnostics[0].message.startswith("None:")


def test_json_requests_validate_the_typed_default_descriptor_path() -> None:
    from pathlib import PurePosixPath

    from datamimic_ce.authoring.domain.requests import CompileDocumentRequest, DecompileDocumentRequest

    for model, payload in (
        (CompileDocumentRequest, {"document": _document()}),
        (DecompileDocumentRequest, {"xml": "<setup/>"}),
    ):
        result = model.model_validate_json(json.dumps(payload))
        assert result.descriptor_path == PurePosixPath("model.xml")
        assert result.model_dump(mode="json")["descriptor_path"] == "model.xml"


def test_discriminator_diagnostics_do_not_echo_secrets(tmp_path: Path) -> None:
    from datamimic_ce.authoring.domain.requests import RejectedBuild

    result = _build_with_acceptance(tmp_path, json.dumps({"expectations": [{"kind": "private-token"}]}))
    assert isinstance(result, RejectedBuild), result
    assert "private-token" not in result.model_dump_json()
    assert result.diagnostics[0].path == ("expectations", 0)


@pytest.mark.parametrize(
    "patch",
    [
        {"max_count": 0},
        {"max_count": 1001},
        {"max_count": True},
        {"max_count": "3"},
        {"timeout_seconds": 0},
        {"sample_size": -1},
        {"sample_size": True},
        {"unknown_field": 1},
        {"document": _document()},
        {"descriptor_path": "model.xml"},
    ],
)
def test_canonical_build_rejects_invalid_bounds_and_unknown_fields(tmp_path: Path, patch: dict) -> None:
    from datamimic_ce.authoring.domain.diagnostics import DiagnosticPhase
    from datamimic_ce.authoring.domain.requests import RejectedBuild

    result = _build_with_acceptance(tmp_path, json.dumps(patch))
    assert isinstance(result, RejectedBuild), result
    assert result.phase is DiagnosticPhase.MODEL
    assert result.diagnostics[0].path == tuple(patch)
