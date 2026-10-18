"""Build preserves proof requests and rejects dishonest transport values."""

import pytest
from pydantic import ValidationError


def _document() -> dict:
    return {"version": "1", "root": {"kind": "setup", "properties": {"rngSeed": 7}, "children": []}}


def test_build_uses_transaction_expectations_and_ce_verification() -> None:
    from datamimic_ce.authoring.domain.requests import BuildRequestV4

    request = BuildRequestV4.model_validate(
        {
            "document": _document(),
            "expectations": [{"kind": "exact_count", "subject": {"kind": "product", "product": "cities"}, "count": 3}],
            "verification": {"smoke_export": True, "deterministic_replay": True},
        }
    )
    assert request.version == "4.0"
    assert request.expectations[0].count == 3
    assert request.verification.smoke_export is True
    assert request.verification.deterministic_replay is True
    assert "expectations" not in request.document.model_dump(mode="json")


def test_build_rejects_duplicate_expectations() -> None:
    from datamimic_ce.authoring.domain.requests import BuildRequestV4

    expectation = {"kind": "exact_count", "subject": {"kind": "product", "product": "cities"}, "count": 3}
    with pytest.raises(ValidationError, match="unique"):
        BuildRequestV4.model_validate({"document": _document(), "expectations": [expectation, expectation]})


def test_role_and_caller_origin_survive_transport() -> None:
    from datamimic_ce.authoring.domain.requests import BuildRequestV4

    request = BuildRequestV4.model_validate(
        {
            "document": _document(),
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
    from datamimic_ce.authoring.domain.requests import BuildRequestV4

    request = BuildRequestV4.model_validate(
        {
            "document": _document(),
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
                    "document": _document(),
                    "compiled_xml": "<setup/>",
                    "expectations_sha256": "0" * 64,
                    "xml_sha256": "0" * 64,
                    "semantic_sha256": "0" * 64,
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


def test_validation_diagnostics_omit_input_secrets_and_none_prefix() -> None:
    from datamimic_ce.authoring.domain.requests import BuildRequestV4, RejectedBuild

    try:
        BuildRequestV4.model_validate({"version": "a-private-token", "document": _document()})
    except ValidationError as error:
        rejection = RejectedBuild.from_model_validation(error)
    else:
        pytest.fail("wrong protocol version was accepted")
    assert rejection.diagnostics[0].path == ("version",)
    assert "a-private-token" not in rejection.model_dump_json()
    assert not rejection.diagnostics[0].message.startswith("None:")


def test_json_requests_validate_the_typed_default_descriptor_path() -> None:
    import json
    from pathlib import PurePosixPath
    from datamimic_ce.authoring.domain.requests import BuildRequestV4, CompileDocumentRequest, DecompileDocumentRequest

    for model, payload in (
        (BuildRequestV4, {"document": _document()}),
        (CompileDocumentRequest, {"document": _document()}),
        (DecompileDocumentRequest, {"xml": "<setup/>"}),
    ):
        result = model.model_validate_json(json.dumps(payload))
        assert result.descriptor_path == PurePosixPath("model.xml")
        assert result.model_dump(mode="json")["descriptor_path"] == "model.xml"


def test_discriminator_diagnostics_do_not_echo_secrets() -> None:
    from datamimic_ce.authoring.domain.requests import BuildRequestV4, RejectedBuild

    with pytest.raises(ValidationError) as error:
        BuildRequestV4.model_validate({"document": _document(), "expectations": [{"kind": "private-token"}]})
    result = RejectedBuild.from_model_validation(error.value)
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
    ],
)
def test_canonical_build_rejects_invalid_bounds_and_unknown_fields(patch: dict) -> None:
    from datamimic_ce.authoring.domain.requests import BuildRequestV4

    with pytest.raises(ValidationError):
        BuildRequestV4.model_validate({"document": _document(), **patch})
