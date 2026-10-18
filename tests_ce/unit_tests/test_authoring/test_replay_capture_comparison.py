"""Full replay comparison distinguishes structure, ordering and passive value types."""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.build_verification import compare_captures
from datamimic_ce.authoring.domain.capture import CapturedProduct, CapturedProducts
from datamimic_ce.authoring.domain.proof import ReplayMismatchKind, VerificationGateStatus
from datamimic_ce.authoring.domain.requests import BuildRequestV4, RejectedBuild


def _capture(**products: tuple[object, ...]) -> CapturedProducts:
    return CapturedProducts(tuple(CapturedProduct(name, rows) for name, rows in products.items()), 10)


@pytest.mark.parametrize(
    ("first", "replay", "kind", "index"),
    [
        (_capture(items=({"id": 1},)), _capture(), ReplayMismatchKind.MISSING_PRODUCT, None),
        (_capture(), _capture(items=({"id": 1},)), ReplayMismatchKind.UNEXPECTED_PRODUCT, None),
        (_capture(items=({"id": 1}, {"id": 2})), _capture(items=({"id": 1},)), ReplayMismatchKind.ROW_COUNT, 1),
        (_capture(items=({"id": 1},)), _capture(items=({"id": 1}, {"id": 2})), ReplayMismatchKind.ROW_COUNT, 1),
        (
            _capture(items=({"id": 1}, {"id": 2})),
            _capture(items=({"id": 2}, {"id": 1})),
            ReplayMismatchKind.ROW_CONTENT,
            0,
        ),
        (
            _capture(items=({"id": 1}, {"id": 2})),
            _capture(items=({"id": 1}, {"id": 99})),
            ReplayMismatchKind.ROW_CONTENT,
            1,
        ),
    ],
    ids=["missing-product", "extra-product", "shorter-prefix", "longer-prefix", "row-order", "later-row"],
)
def test_replay_reports_structural_differences(first, replay, kind, index) -> None:
    mismatches = compare_captures(first, replay)
    assert len(mismatches) == 1
    assert mismatches[0].kind is kind
    assert mismatches[0].first_difference == index


@pytest.mark.parametrize(
    ("first", "replay"),
    [
        (1, True),
        (0, False),
        (1, 1.0),
        (Decimal("1"), 1),
        ([1], [True]),
        ({"nested": [{"v": 1}]}, {"nested": [{"v": True}]}),
        ((1,), [1]),
    ],
)
def test_replay_rejects_equal_values_with_different_types(first, replay) -> None:
    mismatches = compare_captures(_capture(items=({"v": first},)), _capture(items=({"v": replay},)))
    assert len(mismatches) == 1
    assert mismatches[0].kind is ReplayMismatchKind.ROW_CONTENT


def test_replay_preserves_passive_values_and_ignores_object_key_order() -> None:
    first = {"id": 1, "nested": [Decimal("1.5"), date(2026, 1, 1), datetime(2026, 1, 1), None]}
    replay = {"nested": [Decimal("1.5"), date(2026, 1, 1), datetime(2026, 1, 1), None], "id": 1}
    assert compare_captures(_capture(items=(first,)), _capture(items=(replay,))) == ()


def test_real_build_rejects_type_changing_replay(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    marker = tmp_path / "first-run"
    request = BuildRequestV4.model_validate(
        {
            "document": {
                "root": {
                    "kind": "setup",
                    "properties": {"rng_seed": 7},
                    "children": [
                        {
                            "kind": "generate",
                            "properties": {"name": "items", "count": 1},
                            "children": [
                                {
                                    "kind": "key",
                                    "properties": {
                                        "name": "value",
                                        "script": f"True if os.path.exists({str(marker)!r}) else (os.mkdir({str(marker)!r}), 1)[1]",
                                    },
                                },
                            ],
                        },
                    ],
                }
            },
            "verification": {"deterministic_replay": True},
        }
    )
    result = create_authoring_application(workspace_root=workspace).build(request)
    assert isinstance(result, RejectedBuild), result
    assert marker.is_dir()
    assert result.verification.deterministic_replay.status is VerificationGateStatus.FAILED
    assert result.verification.deterministic_replay.mismatches[0].kind is ReplayMismatchKind.ROW_CONTENT
