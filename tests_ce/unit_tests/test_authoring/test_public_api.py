import inspect
import json

import datamimic_ce.authoring.contracts as contracts
from datamimic_ce.authoring import api, service
from datamimic_ce.authoring.diagnostics import LintResult
from datamimic_ce.authoring.rule_catalog import RuleSeverity
from datamimic_ce.authoring.service import scaffold
from datamimic_ce.authoring.spec import ExactCountExpectation, ExpectationIntent
from datamimic_ce.engine.runtime.api import Context, SetupContext
from datamimic_ce.engine.runtime.contexts.context import Context as InternalContext
from datamimic_ce.engine.runtime.contexts.setup_context import SetupContext as InternalSetupContext


def test_authoring_api_has_typed_signatures_and_delegates(monkeypatch) -> None:
    for public_function, service_function in (
        (api.capabilities, service.capabilities),
        (api.check, service.check),
        (api.reference, service.reference),
        (api.run, service.run),
        (api.scaffold, service.scaffold),
    ):
        assert inspect.signature(public_function) == inspect.signature(service_function)

    request = object()
    result = object()
    received: list[object] = []

    def fake_check(actual_request):
        received.append(actual_request)
        return result

    monkeypatch.setattr(service, "check", fake_check)
    assert api.check(request) is result
    assert received == [request]


def test_public_contract_exports_preserve_identity() -> None:
    assert contracts.ExpectationIntent is ExpectationIntent
    assert contracts.LintResult is LintResult
    assert contracts.RuleSeverity is RuleSeverity


def test_runtime_api_exports_context_types_by_identity() -> None:
    assert Context is InternalContext
    assert SetupContext is InternalSetupContext


def test_scaffold_document_keeps_json_shape() -> None:
    raw_spec = {"version": "1", "products": []}
    document = contracts.AuthoringDocument.model_construct(root=raw_spec)
    request = contracts.ScaffoldRequest(spec=document)

    assert request.spec is document
    assert request.spec.root is raw_spec
    assert request.model_dump(mode="json")["spec"] == raw_spec
    assert json.loads(request.model_dump_json())["spec"] == raw_spec
    validated = contracts.ScaffoldRequest.model_validate_json(json.dumps({"spec": raw_spec}))
    assert validated.spec.root == raw_spec
    assert contracts.ScaffoldRequest.model_json_schema()["properties"]["spec"] == {
        "description": "Versioned AuthoringSpecV1 model.dm.json intent.",
        "title": "Spec",
        "type": "object",
    }


def test_scaffold_document_shallow_copies_outer_dict_only() -> None:
    nested_products = [{"kind": "generated", "name": "items", "count": 1}]
    raw_spec = {"version": "1", "products": nested_products}
    request = contracts.ScaffoldRequest(spec=raw_spec)

    assert request.spec.root is not raw_spec
    assert request.spec.root["products"] is nested_products
    assert request.spec.root["products"][0] is nested_products[0]


def test_non_json_document_value_is_rejected_by_scaffold_validation() -> None:
    request = contracts.ScaffoldRequest(spec={"version": "1", "products": [object()]})

    result = scaffold(request)

    assert not result.ok
    assert result.stage is contracts.AuthoringStage.RENDER
    assert result.issues[0].message == "Input should be a valid dictionary or object to extract fields from"


def test_scaffold_expectation_keeps_json_shape() -> None:
    raw_spec = {"version": "1", "products": []}
    raw_expectation = {"kind": "exact_count", "product": "items", "count": 2}
    request = contracts.ScaffoldRequest(spec=raw_spec, acceptance_requirements=[raw_expectation])

    assert isinstance(request.acceptance_requirements[0], contracts.AuthoringExpectation)
    assert isinstance(request.acceptance_requirements[0].root, ExactCountExpectation)
    assert request.model_dump(mode="json")["acceptance_requirements"] == [
        {"kind": "exact_count", "product": "items", "count": 2, "list_field": None}
    ]
    assert json.loads(request.model_dump_json())["acceptance_requirements"] == [
        {"kind": "exact_count", "product": "items", "count": 2, "list_field": None}
    ]
    schema = contracts.ScaffoldRequest.model_json_schema()
    item_schema = schema["properties"]["acceptance_requirements"]["items"]
    assert item_schema["discriminator"]["propertyName"] == "kind"
    assert len(item_schema["oneOf"]) == 7
