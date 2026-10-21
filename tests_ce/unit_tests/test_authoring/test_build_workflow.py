"""Orchestration counterexamples; the actual runtime is covered separately."""
from dataclasses import dataclass, field

import pytest

from datamimic_ce.authoring.domain.capture import CapturedProduct, CapturedProducts, ProductCaptureEvidence, CaptureStatus
from datamimic_ce.authoring.domain.requests import BuildRequestV4, BoundedExecutionEvidence, IncludeGraphResult, LintResult


def request(**overrides):
    data = {"document": {"root": {"kind": "setup", "properties": {"rngSeed": 7}, "children": [
        {"kind": "generate", "properties": {"name": "cities", "count": 3}, "children": [
            {"kind": "key", "properties": {"name": "id", "constant": "1"}}]}]}}}
    data.update(overrides)
    return BuildRequestV4.model_validate(data)


def captured(*, rows=({"id": 1}, {"id": 2}, {"id": 3}), complete=True):
    return BoundedExecutionEvidence(ok=True, captured=CapturedProducts((CapturedProduct("cities", tuple(rows),
        ProductCaptureEvidence(status=CaptureStatus.COMPLETE if complete else CaptureStatus.CAPPED,
            requested=len(rows), observed=len(rows), limit=10 if complete else len(rows), reason="test provenance")),), 10))


class Validator:
    def validate(self, xml, *, descriptor_path=None):
        return LintResult(ok=True)

    def include_graph(self, xml):
        return IncludeGraphResult(ok=True)


class Policy:
    def diagnostics(self, document):
        return ()


@dataclass
class Executor:
    replies: list
    calls: list = field(default_factory=list)
    def execute(self, request):
        self.calls.append(request)
        return self.replies.pop(0)


def workflow(executor):
    from datamimic_ce.authoring.adapters.dm_json_codec import CeDmJsonCodec
    from datamimic_ce.authoring.application.build import BuildDocumentWorkflow
    return BuildDocumentWorkflow(CeDmJsonCodec(), Validator(), executor, Policy())


def test_ready_uses_full_capture_and_one_execution():
    executor = Executor([captured()])
    result = workflow(executor).execute(request(sample_rows=1))
    assert result.outcome == "ready"
    assert result.evidence[0].count == 3
    assert len(result.evidence[0].rows) == 1
    assert result.evidence[0].capture.complete
    assert result.verification.deterministic_replay.status.value == "not_requested"
    assert len(executor.calls) == 1


def test_derived_count_cannot_be_omitted_by_caller():
    result = workflow(Executor([captured(rows=({"id": 1}, {"id": 2}))])).execute(request())
    assert result.outcome == "rejected"
    assert result.phase.value == "evidence"


def test_replay_compares_rows_beyond_response_samples():
    first = captured()
    second = captured(rows=({"id": 1}, {"id": 2}, {"id": 999}))
    executor = Executor([first, second])
    result = workflow(executor).execute(request(sample_rows=1, verification={"deterministic_replay": True}))
    assert result.outcome == "rejected"
    assert result.verification.deterministic_replay.status.value == "failed"
    assert result.verification.deterministic_replay.mismatches[0].first_difference == 2
    assert len(executor.calls) == 2


def test_passing_replay_does_not_erase_incomplete_first_capture():
    executor = Executor([captured(complete=False), captured()])
    result = workflow(executor).execute(request(verification={"deterministic_replay": True}))
    assert result.outcome == "rejected"
    assert result.verification.deterministic_replay.status.value == "blocked"
    assert len(executor.calls) == 1


def test_unseeded_replay_fails():
    task = request(verification={"deterministic_replay": True})
    task = task.model_copy(update={"document": task.document.model_copy(update={"root": task.document.root.model_copy(update={"properties": {}})})})
    result = workflow(Executor([captured()])).execute(task)
    assert result.outcome == "rejected"
    assert result.verification.deterministic_replay.status.value == "failed"


def test_missing_capture_never_ready_even_without_expectations():
    result = workflow(Executor([BoundedExecutionEvidence(ok=True, captured=CapturedProducts((), 10))])).execute(request())
    assert result.outcome == "rejected"


def test_caller_requirement_is_not_replaced_by_derived_check():
    task = request(acceptance_requirements=[{"origin": "caller", "expectation": {
        "kind": "exact_count", "subject": {"kind": "product", "product": "cities"}, "count": 2}}])
    result = workflow(Executor([captured()])).execute(task)
    assert result.outcome == "rejected"
    assert any(diagnostic.path[:1] == ("acceptance_requirements",) for diagnostic in result.diagnostics)
