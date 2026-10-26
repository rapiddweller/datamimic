"""Orchestration counterexamples; the actual runtime is covered separately."""

from dataclasses import dataclass, field

from datamimic_ce.authoring.domain.capture import (
    CapturedProduct,
    CapturedProducts,
    CaptureStatus,
    ProductCaptureEvidence,
)
from datamimic_ce.authoring.domain.requests import (
    PROJECT_ACCEPTANCE_PATH,
    PROJECT_ENTRY_PATH,
    BoundedExecutionEvidence,
    BuildRequestV5,
    IncludeGraphResult,
    LintResult,
)

SEEDED = '<setup rngSeed="7"><generate name="cities" count="3"><key name="id" constant="1"/></generate></setup>'


def captured(*, rows=({"id": 1}, {"id": 2}, {"id": 3}), complete=True):
    return BoundedExecutionEvidence(
        ok=True,
        captured=CapturedProducts(
            (
                CapturedProduct(
                    "cities",
                    tuple(rows),
                    ProductCaptureEvidence(
                        status=CaptureStatus.COMPLETE if complete else CaptureStatus.CAPPED,
                        requested=len(rows),
                        observed=len(rows),
                        limit=10 if complete else len(rows),
                        reason="test provenance",
                    ),
                ),
            ),
            10,
        ),
    )


class Validator:
    def validate(self, xml, *, descriptor_path=None):
        return LintResult(ok=True)

    def include_graph(self, xml):
        return IncludeGraphResult(ok=True)


class Policy:
    def diagnostics(self, document, project=()):
        return ()


@dataclass
class Executor:
    replies: list
    calls: list = field(default_factory=list)

    def execute(self, request):
        self.calls.append(request)
        return self.replies.pop(0)


@dataclass
class Files:
    entry: str
    acceptance: BuildRequestV5

    def read_project_file(self, path):
        files = {PROJECT_ENTRY_PATH: self.entry, PROJECT_ACCEPTANCE_PATH: self.acceptance.model_dump_json()}
        return files[path].encode()


def workflow(executor, entry=SEEDED, **acceptance):
    from datamimic_ce.authoring.adapters.dm_json_codec import CeDmJsonCodec
    from datamimic_ce.authoring.application.build import BuildDocumentWorkflow

    files = Files(entry, BuildRequestV5.model_validate(acceptance))
    return BuildDocumentWorkflow(CeDmJsonCodec(), Validator(), executor, Policy(), files)


def test_ready_uses_full_capture_and_one_execution():
    executor = Executor([captured()])
    result = workflow(executor, SEEDED.replace(' rngSeed="7"', ""), sample_rows=1).execute()
    assert result.outcome == "ready"
    assert result.evidence[0].count == 3
    assert len(result.evidence[0].rows) == 1
    assert result.evidence[0].capture.complete
    assert result.verification.deterministic_replay.status.value == "not_requested"
    assert len(executor.calls) == 1


def test_a_seeded_build_always_replays_under_three_other_hash_seeds():
    executor = Executor([captured() for _ in range(4)])
    result = workflow(executor).execute()
    assert result.outcome == "ready"
    assert result.verification.deterministic_replay.status.value == "passed"
    assert [call.hash_seed for call in executor.calls] == [1, 2, 3, 4]


def test_a_differing_replay_stops_the_replays_and_names_a_possible_cause():
    from datamimic_ce.authoring.domain.script_semantics import ReplayCause

    executor = Executor([captured(), captured(rows=({"id": 1}, {"id": 2}, {"id": 999}))])
    result = workflow(executor).execute()
    assert result.outcome == "rejected"
    assert result.verification.deterministic_replay.status.value == "failed"
    assert len(executor.calls) == 2
    assert ReplayCause.OTHER.failure_message() in [item.message for item in result.diagnostics]


def test_derived_count_cannot_be_omitted_by_caller():
    result = workflow(Executor([captured(rows=({"id": 1}, {"id": 2}))])).execute()
    assert result.outcome == "rejected"
    assert result.phase.value == "evidence"


def test_replay_compares_rows_beyond_response_samples():
    first = captured()
    second = captured(rows=({"id": 1}, {"id": 2}, {"id": 999}))
    executor = Executor([first, second])
    result = workflow(executor, sample_rows=1, verification={"deterministic_replay": True}).execute()
    assert result.outcome == "rejected"
    assert result.verification.deterministic_replay.status.value == "failed"
    assert result.verification.deterministic_replay.mismatches[0].first_difference == 2
    assert len(executor.calls) == 2


def test_passing_replay_does_not_erase_incomplete_first_capture():
    executor = Executor([captured(complete=False), captured()])
    result = workflow(executor, verification={"deterministic_replay": True}).execute()
    assert result.outcome == "rejected"
    assert result.verification.deterministic_replay.status.value == "blocked"
    assert len(executor.calls) == 1


def test_unseeded_replay_fails():
    unseeded = SEEDED.replace(' rngSeed="7"', "")
    result = workflow(Executor([captured()]), unseeded, verification={"deterministic_replay": True}).execute()
    assert result.outcome == "rejected"
    assert result.verification.deterministic_replay.status.value == "failed"


def test_missing_capture_never_ready_even_without_expectations():
    result = workflow(Executor([BoundedExecutionEvidence(ok=True, captured=CapturedProducts((), 10))])).execute()
    assert result.outcome == "rejected"


def test_caller_requirement_is_not_replaced_by_derived_check():
    result = workflow(
        Executor([captured()]),
        acceptance_requirements=[
            {
                "origin": "caller",
                "expectation": {"kind": "exact_count", "subject": {"kind": "product", "product": "cities"}, "count": 2},
            }
        ],
    ).execute()
    assert result.outcome == "rejected"
    assert any(diagnostic.path[:1] == ("acceptance_requirements",) for diagnostic in result.diagnostics)


def test_entry_the_codec_cannot_read_is_rejected_before_execution():
    executor = Executor([])
    result = workflow(executor, entry="<setup><not-a-dsl-element/></setup>").execute()
    assert result.outcome == "rejected"
    assert result.phase.value == "decompile"
    assert executor.calls == []


def test_a_file_that_changed_while_build_read_it_rejects_the_build():
    from datamimic_ce.authoring.domain.requests import ProjectFileDigest

    changed = captured()
    changed = BoundedExecutionEvidence(
        ok=changed.ok,
        captured=changed.captured,
        files=(ProjectFileDigest(path=PROJECT_ENTRY_PATH, sha256="0" * 64),),
    )
    result = workflow(Executor([changed, *(captured() for _ in range(3))])).execute()
    assert result.outcome == "rejected"
    assert result.phase.value == "evidence"
    assert any(item.path == ("project", "datamimic.xml") for item in result.diagnostics), result.diagnostics
