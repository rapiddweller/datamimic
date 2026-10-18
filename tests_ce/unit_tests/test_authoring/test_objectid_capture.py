"""Only known BSON identifiers are projected at the child capture boundary."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from bson import ObjectId

from datamimic_ce.authoring.adapters import dryrun
from datamimic_ce.authoring.domain.capture import CapturedObjectId, validate_capture_values


_ID = ObjectId("507f1f77bcf86cd799439011")
_CAPTURE_ID = CapturedObjectId(value=str(_ID))


def test_projection_copies_containers_and_preserves_native_scalars():
    leaves = (date(2026, 1, 1), datetime(2026, 1, 1), Decimal("1.20"), UUID(int=7))
    original = {"rows": [{"id": _ID, "nested": (_ID, {"values": [_ID]}), "native": leaves}]}
    projected = dryrun._project_capture_object_ids(original)
    assert projected is not original
    assert projected["rows"] is not original["rows"]
    row = projected["rows"][0]
    assert row["id"] == _CAPTURE_ID
    assert row["nested"] == (_CAPTURE_ID, {"values": [_CAPTURE_ID]})
    assert isinstance(row["native"], tuple)
    assert all(actual is expected for actual, expected in zip(row["native"], leaves))
    assert original["rows"][0]["id"] is _ID
    validate_capture_values(projected)


class _Unsupported:
    def __str__(self):
        raise AssertionError("must not stringify unknown values")

    def __repr__(self):
        raise AssertionError("must not represent unknown values")

    def __reduce__(self):
        raise AssertionError("must not pickle unknown values")


@pytest.mark.parametrize(
    "value",
    [_Unsupported(), float("nan"), Decimal("Infinity"), 1 << 14001, {1: "x"}],
    ids=["unknown", "nan", "infinity", "large_integer", "non_string_key"],
)
def test_projection_keeps_strict_rejection(value):
    with pytest.raises(ValueError):
        dryrun._validated_capture_rows(dryrun._project_capture_object_ids({"rows": [{"value": value}]}))


def test_projection_rejects_cycles_before_recursing():
    value = []
    value.append(value)
    with pytest.raises(ValueError, match="cyclic"):
        dryrun._project_capture_object_ids(value)


def test_projection_rejects_depth_before_recursing():
    value = _ID
    for _ in range(65):
        value = [value]
    with pytest.raises(ValueError, match="depth"):
        dryrun._project_capture_object_ids(value)


def test_projection_checks_item_budget_before_visiting_leaves(monkeypatch):
    monkeypatch.setattr(dryrun, "MAX_CAPTURE_ITEMS", 3)
    with pytest.raises(ValueError, match="item"):
        dryrun._project_capture_object_ids([_Unsupported()] * 4)
    assert dryrun._project_capture_object_ids([_ID, _ID]) == [_CAPTURE_ID, _CAPTURE_ID]


def test_projection_counts_shared_containers_each_time(monkeypatch):
    monkeypatch.setattr(dryrun, "MAX_CAPTURE_ITEMS", 4)
    shared = [_ID]
    with pytest.raises(ValueError, match="item"):
        dryrun._project_capture_object_ids([shared, shared])


def test_strict_capture_and_parent_decoder_still_reject_object_id():
    import pickle

    with pytest.raises(ValueError):
        dryrun._validated_capture_rows({"rows": [{"id": _ID}]})
    with pytest.raises(pickle.UnpicklingError):
        dryrun._decode_worker_payload(pickle.dumps(_ID))


def test_child_core_projects_full_capture_and_public_samples(tmp_path, monkeypatch):
    import pickle
    from datamimic_ce.engine.runtime.lifecycle.runner import RuntimeRunSession
    from datamimic_ce.authoring.projection.evidence import sample_evidence

    native_capture = {
        "rows": [
            {"id": _ID, "nested": {"ids": [_ID]}},
            {"id": _ID, "nested": {"ids": [_ID]}},
        ]
    }
    monkeypatch.setattr(RuntimeRunSession, "capture_test_result", lambda self: native_capture)
    path = tmp_path / "model.xml"
    path.write_text(
        '<setup rngSeed="7"><generate name="rows" count="2"><key name="id" constant="1"/></generate></setup>'
    )
    result = dryrun._run_engine_capture(path, 10, False, False, profile_loader=lambda *_: {})
    assert isinstance(result, dryrun._WorkerSuccess), result
    decoded = dryrun._decode_worker_message(pickle.dumps(result))
    assert isinstance(decoded, dryrun._WorkerSuccess)
    assert len(decoded.captured["rows"]) == 2
    assert all(row == {"id": _CAPTURE_ID, "nested": {"ids": [_CAPTURE_ID]}} for row in decoded.captured["rows"])
    captured = dryrun._captured_products(decoded, 10)
    product = captured.get("rows")
    assert product.capture.complete
    samples = sample_evidence(captured, 1)
    assert samples[0].count == 2
    assert samples[0].rows == ({"id": str(_ID), "nested": {"ids": [str(_ID)]}},)
    assert all(row["id"] is _ID and row["nested"]["ids"][0] is _ID for row in native_capture["rows"])


def test_replay_keeps_bson_identity_beyond_response_sample():
    from datamimic_ce.authoring.domain.build_verification import compare_captures
    from datamimic_ce.authoring.domain.capture import CapturedProduct, CapturedProducts
    from datamimic_ce.authoring.domain.proof import ReplayMismatchKind
    from datamimic_ce.authoring.projection.evidence import sample_evidence

    def capture(second):
        rows = dryrun._validated_capture_rows(
            dryrun._project_capture_object_ids({"items": [{"id": "same first row"}, {"id": second}]})
        )
        return CapturedProducts(products=(CapturedProduct(name="items", rows=rows["items"]),), max_count=10)

    first = capture(_ID)
    same = capture(ObjectId(str(_ID)))
    changed_type = capture(str(_ID))
    assert sample_evidence(first, 1) == sample_evidence(changed_type, 1)
    assert compare_captures(first, same) == ()
    mismatches = compare_captures(first, changed_type)
    assert len(mismatches) == 1
    assert mismatches[0].kind is ReplayMismatchKind.ROW_CONTENT
    assert mismatches[0].first_difference == 1


@pytest.mark.parametrize("value", ["not-an-id", "A" * 24, "a" * 25, "a" * 23 + "\n", 123])
def test_owned_object_id_rejects_noncanonical_values(value):
    with pytest.raises(ValueError):
        CapturedObjectId(value=value)


@pytest.mark.parametrize("field,value", [("value", "invalid"), ("surplus", "forged")])
def test_owned_object_id_revalidates_complete_forged_state(field, value):
    import pickle

    forged = CapturedObjectId(value=str(_ID))
    object.__setattr__(forged, field, value)
    decoded = dryrun._decode_worker_payload(pickle.dumps(forged))
    with pytest.raises(ValueError):
        dryrun._validated_capture_rows({"rows": [{"id": decoded}]})


def test_owned_object_id_is_immutable_and_retains_identity_through_passive_decoder():
    import pickle

    from dataclasses import FrozenInstanceError

    with pytest.raises(FrozenInstanceError):
        _CAPTURE_ID.value = "a" * 24
    decoded = dryrun._decode_worker_payload(pickle.dumps(_CAPTURE_ID))
    assert type(decoded) is CapturedObjectId
    assert decoded == _CAPTURE_ID
    assert decoded != str(_ID)
    validate_capture_values(decoded)


def test_smoke_restores_native_bson_at_exporter_boundary(tmp_path, monkeypatch):
    from datamimic_ce.engine.io import api

    received = []

    def export(request):
        received.extend(request.rows)
        return len(request.rows)

    monkeypatch.setattr(api, "smoke_export", export)
    capture = {"items": ({"id": _CAPTURE_ID, "nested": (_CAPTURE_ID, Decimal("1.20"))},)}
    diagnostics, evidence = dryrun._smoke_export(capture, {"items": ("items", [("JSON", {})], ",", "\n")})
    assert diagnostics == []
    assert evidence.attempted_exporters == 1
    assert received == [{"id": _ID, "nested": (_ID, Decimal("1.20"))}]
    assert isinstance(received[0]["id"], ObjectId)
    assert capture["items"][0]["id"] is _CAPTURE_ID


def test_acceptance_display_preserves_object_id_identity():
    from datamimic_ce.authoring.domain.acceptance_evaluation import _display, _duplicate_values, _json_value

    assert _json_value(_CAPTURE_ID) == str(_ID)
    assert _display(_CAPTURE_ID) != _display(str(_ID))
    assert _duplicate_values((_CAPTURE_ID, str(_ID))) == ()
    assert _duplicate_values((_CAPTURE_ID, CapturedObjectId(value=str(_ID)))) == (_CAPTURE_ID,)


@pytest.mark.parametrize(
    "field,value",
    [
        ("__pydantic_private__", {"forged": True}),
        ("__pydantic_extra__", {}),
        ("__pydantic_fields_set__", {"unrelated"}),
    ],
)
def test_owned_object_id_rejects_forged_model_metadata(field, value):
    import pickle

    forged = CapturedObjectId(value=str(_ID))
    object.__setattr__(forged, field, value)
    decoded = dryrun._decode_worker_payload(pickle.dumps(forged))
    with pytest.raises(ValueError):
        dryrun._validated_capture_rows({"rows": [{"id": decoded}]})


def test_user_dictionary_is_not_reinterpreted_as_object_id():
    source = {"rows": [{"nested": {"value": str(_ID)}}]}
    result = dryrun._validated_capture_rows(dryrun._project_capture_object_ids(source))
    assert type(result["rows"][0]["nested"]) is dict
    assert result["rows"][0]["nested"] == source["rows"][0]["nested"]


def test_real_json_smoke_export_accepts_owned_object_ids():
    diagnostics, evidence = dryrun._smoke_export(
        {"items": ({"id": _CAPTURE_ID, "nested": {"ids": [_CAPTURE_ID]}},)},
        {"items": ("items", [("JSON", {})], ",", "\n")},
    )
    assert diagnostics == []
    assert evidence.attempted_exporters == 1
    assert evidence.failed_exporters == 0


def test_owned_object_id_rejects_missing_value_after_unpickle():
    import pickle

    forged = CapturedObjectId(value=str(_ID))
    object.__delattr__(forged, "value")
    decoded = dryrun._decode_worker_payload(pickle.dumps(forged))
    with pytest.raises(ValueError):
        dryrun._validated_capture_rows({"rows": [{"id": decoded}]})


def test_object_id_subclasses_cannot_run_custom_serializers():
    class UntrustedObjectId(ObjectId):
        def __str__(self):
            raise AssertionError("subclass serializer must not run")

    with pytest.raises(ValueError):
        dryrun._validated_capture_rows(
            dryrun._project_capture_object_ids({"rows": [{"id": UntrustedObjectId(str(_ID))}]})
        )


def test_type_adapter_preserves_owned_object_id_class():
    rows = dryrun._validated_capture_rows({"rows": [{"id": _CAPTURE_ID}]})
    assert type(rows["rows"][0]["id"]) is CapturedObjectId
