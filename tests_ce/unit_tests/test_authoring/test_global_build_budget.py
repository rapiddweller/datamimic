"""Build limits all captured product rows in one runtime execution."""

from pathlib import Path
from pathlib import PurePosixPath

import pytest

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.proof import VerificationGateStatus
from datamimic_ce.authoring.domain.requests import BuildRequestV4, DecompileDocumentRequest
from datamimic_ce.engine.runtime.api import create_run_session
from datamimic_ce.engine.runtime.contracts import RunRequest
from datamimic_ce.errors import IssueCode, TaskConfigError


def _build(
    tmp_path: Path,
    xml: str,
    *,
    replay: bool = False,
    smoke: bool = False,
    roles: list[dict] | None = None,
):
    application = create_authoring_application(tmp_path)
    decoded = application.decompile_document(DecompileDocumentRequest(xml=xml))
    assert decoded.outcome == "ready", decoded
    return application.build(
        BuildRequestV4(
            document=decoded.document,
            max_count=5,
            verification={"smoke_export": smoke, "deterministic_replay": replay},
            product_roles=roles or [],
        )
    )


def test_separate_products_share_one_total_budget(tmp_path: Path) -> None:
    result = _build(
        tmp_path,
        '<setup rngSeed="1"><generate name="a" count="3"><key name="id" constant="1"/></generate>'
        '<generate name="b" count="3"><key name="id" constant="2"/></generate></setup>',
    )

    assert result.outcome == "rejected"
    assert any(
        diagnostic.ce_error is not None and diagnostic.ce_error.issue_code is IssueCode.TASK_TOTAL_ROW_BUDGET_EXCEEDED
        for diagnostic in result.diagnostics
    )


def test_included_products_share_one_total_budget(tmp_path: Path) -> None:
    (tmp_path / "one.xml").write_text(
        '<setup><generate name="one" count="3"><key name="id" constant="1"/></generate></setup>',
        encoding="utf-8",
    )
    (tmp_path / "two.xml").write_text(
        '<setup><generate name="two" count="3"><key name="id" constant="2"/></generate></setup>',
        encoding="utf-8",
    )
    xml = '<setup><include uri="one.xml"/><include uri="two.xml"/></setup>'
    application = create_authoring_application(tmp_path, descriptor_path=PurePosixPath("entry.xml"))
    decoded = application.decompile_document(
        DecompileDocumentRequest(xml=xml, descriptor_path=PurePosixPath("entry.xml"))
    )
    assert decoded.outcome == "ready", decoded

    result = application.build(BuildRequestV4(document=decoded.document, max_count=5))

    assert result.outcome == "rejected"


def test_parent_stop_iteration_releases_only_its_uncommitted_reservation(tmp_path: Path) -> None:
    descriptor = tmp_path / "model.xml"
    descriptor.write_text(
        '<setup rngSeed="1" reportLogging="false">'
        '<generate name="partial" count="2"><key name="n" type="int" min="1" max="1" distribution="step"/>'
        '</generate><generate name="rest" count="4"><key name="id" constant="1"/></generate></setup>',
        encoding="utf-8",
    )
    session = create_run_session(RunRequest(descriptor_path=descriptor, test_mode=True, total_row_limit=5))

    captured = session.execute().captured

    assert captured is not None
    assert {name: len(rows) for name, rows in captured.items()} == {"partial": 1, "rest": 4}


def test_over_budget_candidate_does_not_run_its_row_subtasks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from datamimic_ce.engine.runtime.tasks.values.scalar.key_task import KeyTask

    descriptor = tmp_path / "model.xml"
    descriptor.write_text(
        '<setup rngSeed="1"><generate name="a" count="3"><key name="id" constant="1"/></generate>'
        '<generate name="b" count="3"><key name="id" constant="2"/></generate></setup>',
        encoding="utf-8",
    )
    executed: list[object] = []
    execute = KeyTask.execute

    def count_subtask(self: KeyTask, context: object) -> None:
        executed.append(context)
        execute(self, context)

    monkeypatch.setattr(KeyTask, "execute", count_subtask)
    session = create_run_session(RunRequest(descriptor_path=descriptor, test_mode=True, total_row_limit=5))

    with pytest.raises(TaskConfigError):
        session.execute()

    assert len(executed) == 5


def test_exact_total_budget_succeeds_and_replay_gets_fresh_budget(tmp_path: Path) -> None:
    result = _build(
        tmp_path,
        '<setup rngSeed="1"><generate name="a" count="2" target="JSON"><key name="id" constant="1"/></generate>'
        '<generate name="b" count="3" target="JSON"><key name="id" constant="2"/></generate></setup>',
        replay=True,
        smoke=True,
    )

    assert result.outcome == "ready", result.diagnostics
    assert sum(len(product.rows) for product in result.evidence) == 5
    assert result.verification.deterministic_replay.status is VerificationGateStatus.PASSED
    assert result.verification.smoke_export.status is VerificationGateStatus.PASSED


@pytest.mark.parametrize(
    ("parent_count", "child_count", "outcome"),
    [(3, 1, "rejected"), (1, 4, "ready")],
)
def test_nested_products_share_one_total_budget(
    tmp_path: Path, parent_count: int, child_count: int, outcome: str
) -> None:
    result = _build(
        tmp_path,
        f'<setup rngSeed="1"><generate name="parents" count="{parent_count}">'
        '<key name="id" constant="1"/>'
        f'<generate name="children" count="{child_count}"><key name="parent_id" script="parent.id"/></generate>'
        "</generate></setup>",
        roles=[
            {"product": "parents", "field": "id", "role": {"kind": "identifier"}},
            {
                "product": "children",
                "field": "parent_id",
                "role": {"kind": "foreign_key", "parent_product": "parents", "parent_field": "id"},
            },
        ],
    )

    assert result.outcome == outcome, result.diagnostics
    if outcome == "ready":
        assert sum(len(product.rows) for product in result.evidence) == 5
        assert {product.name: product.capture.limit for product in result.evidence} == {
            "parents": 5,
            "children": 5,
        }
