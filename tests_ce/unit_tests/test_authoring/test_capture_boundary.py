"""Malformed captures cannot reach smoke or acceptance consumers."""

import pytest
import multiprocessing as mp
import pickle

from datamimic_ce.authoring.adapters import dryrun
from datamimic_ce.authoring.domain.capture import SmokeExportCapture


def _budget():
    return dryrun._ProductBudget(
        name="items",
        parent_name=None,
        requested_per_parent=1,
        explicit_count=True,
        count_kind=dryrun._CountBoundaryKind.STATIC,
        source_rows_per_parent=None,
        source_exhaustible=False,
        memstore_source=None,
        source_offset=0,
        cyclic=False,
        output_multiplier=1,
        bounded_without_cap=True,
        cap_applied=False,
        reason="one literal row",
    )


@pytest.mark.parametrize("rows", [(1,), ({"id": 1}, 2)])
def test_smoke_rejects_all_malformed_rows_before_export(rows) -> None:
    with pytest.raises(ValueError, match="row"):
        dryrun._smoke_export({"items": rows}, {})


def _receive(message):
    context = mp.get_context("spawn")
    receive, send = context.Pipe(duplex=False)
    try:
        send.send(message)
        payload = receive.recv_bytes(dryrun._MAX_WORKER_REPLY_BYTES)
        try:
            return dryrun._decode_worker_message(payload)
        except (AttributeError, TypeError, ValueError, pickle.PickleError):
            from datamimic_ce.authoring.adapters.bounded_executor import _decode_reply
            from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest
            from datamimic_ce.authoring.domain.diagnostics import AuthoringSystemDiagnosticCode

            evidence = _decode_reply(payload, BoundedExecutionRequest(xml="<setup/>"))
            assert not evidence.ok
            assert evidence.diagnostics[0].code is AuthoringSystemDiagnosticCode.SERIALIZATION
            return None
    finally:
        send.close()
        receive.close()


def test_valid_worker_capture_keeps_every_row() -> None:
    message = dryrun._WorkerSuccess(
        captured={"items": ({"id": 1},)},
        budgets=(_budget(),),
        smoke_diagnostics=(),
        smoke_export=SmokeExportCapture.not_requested(),
    )
    result = _receive(message)
    assert isinstance(result, dryrun._WorkerSuccess)
    assert result.captured == {"items": ({"id": 1},)}


@pytest.mark.parametrize("rows", [(1,), ({"id": 1}, 2)])
def test_parent_rejects_malformed_rows_before_any_consumer(rows) -> None:
    message = dryrun._WorkerSuccess(
        captured={"items": ({"id": 1},)},
        budgets=(_budget(),),
        smoke_diagnostics=(),
        smoke_export=SmokeExportCapture.not_requested(),
    )
    object.__setattr__(message, "captured", {"items": rows})
    result = _receive(message)
    assert result is None


def test_parent_rejects_missing_capture_provenance() -> None:
    result = _receive(
        dryrun._WorkerSuccess(
            captured={"items": ({"id": 1},)},
            budgets=(),
            smoke_diagnostics=(),
            smoke_export=SmokeExportCapture.not_requested(),
        )
    )
    assert result is None


def test_parent_rejects_negative_provenance_count() -> None:
    message = dryrun._WorkerSuccess(
        captured={"items": ({"id": 1},)},
        budgets=(_budget(),),
        smoke_diagnostics=(),
        smoke_export=SmokeExportCapture.not_requested(),
    )
    object.__setattr__(message.budgets[0], "requested_per_parent", -1)
    result = _receive(message)
    assert result is None


@pytest.mark.parametrize(
    "field,value",
    [("source_offset", -1), ("output_multiplier", 0), ("explicit_count", "true"), ("count_kind", "static")],
)
def test_parent_revalidates_native_budget_fields(field, value):
    message = dryrun._WorkerSuccess(
        captured={"items": ({"id": 1},)},
        budgets=(_budget(),),
        smoke_diagnostics=(),
        smoke_export=SmokeExportCapture.not_requested(),
    )
    object.__setattr__(message.budgets[0], field, value)
    assert _receive(message) is None


def test_parent_rejects_missing_success_fields():
    message = dryrun._WorkerSuccess(
        captured={"items": ({"id": 1},)},
        budgets=(_budget(),),
        smoke_diagnostics=(),
        smoke_export=SmokeExportCapture.not_requested(),
    )
    object.__delattr__(message, "budgets")
    assert _receive(message) is None


def test_parent_rejects_duplicate_or_orphan_provenance():
    message = dryrun._WorkerSuccess(
        captured={"items": ({"id": 1},)},
        budgets=(_budget(), _budget()),
        smoke_diagnostics=(),
        smoke_export=SmokeExportCapture.not_requested(),
    )
    assert _receive(message) is None
    message = dryrun._WorkerSuccess(
        captured={"items": ({"id": 1},)},
        budgets=(_budget(),),
        smoke_diagnostics=(),
        smoke_export=SmokeExportCapture.not_requested(),
    )
    object.__setattr__(message.budgets[0], "parent_name", "missing")
    assert _receive(message) is None


def test_full_nested_capture_limit_uses_actual_parent_total():
    from dataclasses import replace

    parent = replace(_budget(), name="parents", requested_per_parent=2)
    child = replace(_budget(), name="parents|children", parent_name="parents", requested_per_parent=2)
    valid = dryrun._WorkerSuccess(
        captured={"parents": ({"id": 1}, {"id": 2}), "parents|children": ({"id": 1},) * 4},
        budgets=(parent, child),
        smoke_diagnostics=(),
        smoke_export=SmokeExportCapture.not_requested(),
    )
    assert dryrun._validated_worker_success(valid, max_count=2) == valid
    object.__setattr__(valid, "captured", {**valid.captured, "parents|children": ({"id": 1},) * 5})
    with pytest.raises(ValueError, match="nested"):
        dryrun._validated_worker_success(valid, max_count=2)


def test_boundary_rejects_missing_product_capture_even_when_provenance_exists():
    message = dryrun._WorkerSuccess(
        captured={}, budgets=(_budget(),), smoke_diagnostics=(), smoke_export=SmokeExportCapture.not_requested()
    )
    assert _receive(message) is None


def test_passive_decoder_keeps_native_values_and_portable_error_metadata():
    import pickle
    from datetime import date, datetime, timezone
    from decimal import Decimal
    from uuid import UUID
    from datamimic_ce.errors import parser_validation_error
    from datamimic_ce.errors.codes import IssueCode
    from datamimic_ce.errors.context import DescriptorLocation

    row = {
        "decimal": Decimal("1.20"),
        "date": date(2026, 10, 18),
        "time": datetime(2026, 10, 18, tzinfo=timezone.utc),
        "uuid": UUID(int=7),
    }
    success = dryrun._WorkerSuccess(
        captured={"items": (row,)},
        budgets=(_budget(),),
        smoke_diagnostics=(),
        smoke_export=SmokeExportCapture.not_requested(),
    )
    received = _receive(success)
    assert isinstance(received, dryrun._WorkerSuccess)
    assert received.captured["items"][0] == row
    error = parser_validation_error(
        code=IssueCode.PARSER_EXECUTE_INVALID_SOURCE,
        location=DescriptorLocation(element_tag="execute", descriptor_path="nested/model.xml", line=4),
    )
    error.__cause__ = ValueError("invalid source")
    error.validation_errors = ({"loc": ("uri",), "type": "missing", "msg": "Field required"},)
    received_error = _receive(dryrun._WorkerFailure(message=str(error), fix_hint="Repair source.", error=error))
    assert isinstance(received_error, dryrun._WorkerFailure)
    assert type(received_error.error) is type(error)
    assert received_error.error.location == error.location
    assert received_error.error.issue_code is error.issue_code
    assert received_error.error.validation_errors == error.validation_errors
    assert type(received_error.error.__cause__) is ValueError
    assert str(received_error.error.__cause__) == "invalid source"
    assert dryrun._decode_worker_payload(pickle.dumps(success)).captured == success.captured


def test_pickle_reducer_cannot_execute_in_parent(tmp_path):
    import pickle
    from datamimic_ce.authoring.adapters.bounded_executor import _decode_reply
    from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest
    from datamimic_ce.authoring.domain.diagnostics import AuthoringSystemDiagnosticCode

    marker = tmp_path / "escaped"

    class Reducer:
        def __reduce__(self):
            return eval, (f"__import__('pathlib').Path({str(marker)!r}).write_text('escaped')",)

    payload = pickle.dumps(Reducer())
    result = _decode_reply(payload, BoundedExecutionRequest(xml="<setup/>"))
    assert result.diagnostics[0].code is AuthoringSystemDiagnosticCode.SERIALIZATION
    assert _receive(Reducer()) is None
    assert not marker.exists()


def test_parent_rejects_forged_extra_envelope_fields():
    message = dryrun._WorkerSuccess(
        captured={"items": ({"id": 1},)},
        budgets=(_budget(),),
        smoke_diagnostics=(),
        smoke_export=SmokeExportCapture.not_requested(),
    )
    object.__setattr__(message, "unknown", True)
    assert _receive(message) is None


def test_parent_rejects_forged_extra_budget_fields():
    message = dryrun._WorkerSuccess(
        captured={"items": ({"id": 1},)},
        budgets=(_budget(),),
        smoke_diagnostics=(),
        smoke_export=SmokeExportCapture.not_requested(),
    )
    object.__setattr__(message.budgets[0], "unknown", True)
    assert _receive(message) is None


def test_passive_decoder_preserves_real_parser_validation_cause(tmp_path):
    from datamimic_ce.engine.dsl.api import DescriptorParser
    from datamimic_ce.errors import ParserValidationError
    from pydantic import ValidationError

    with pytest.raises(ParserValidationError) as caught:
        DescriptorParser.parse_xml(
            '<setup><generate count="1"/></setup>',
            tmp_path / "model.xml",
            None,
            "production",
            profile_loader=lambda *_: {},
        )
    assert isinstance(caught.value.__cause__, ValidationError)
    received = _receive(dryrun._WorkerFailure(message=str(caught.value), fix_hint="Repair key.", error=caught.value))
    assert isinstance(received.error, ParserValidationError)
    assert isinstance(received.error.__cause__, ValidationError)
    assert received.error.validation_errors == caught.value.validation_errors


def test_decoder_rejects_every_other_attribute_lookup():
    import pickle

    class Lookup:
        def __reduce__(self):
            from pydantic import ValidationError

            return getattr, (ValidationError, "__mro__")

    with pytest.raises(pickle.UnpicklingError, match="unsupported attribute"):
        dryrun._decode_worker_payload(pickle.dumps(Lookup()))


def test_cycles_and_deep_captures_fail_before_consumers():
    cyclic = []
    cyclic.append(cyclic)
    for value in (cyclic, [[[[[]]]]]):
        if value is not cyclic:
            for _ in range(70):
                value = [value]
        message = dryrun._WorkerSuccess(
            captured={"items": ({"value": 1},)},
            budgets=(_budget(),),
            smoke_diagnostics=(),
            smoke_export=SmokeExportCapture.not_requested(),
        )
        object.__setattr__(message, "captured", {"items": ({"value": value},)})
        assert _receive(message) is None
        with pytest.raises(ValueError):
            dryrun._smoke_export(message.captured, {})


def test_vendor_cause_normalization_is_transport_only(tmp_path):
    import pickle
    from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
    from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig
    from datamimic_ce.engine.io.api import normalize_error_cause_for_transport
    from datamimic_ce.errors import OperationError, ExternalFailureCause
    from sqlalchemy.exc import OperationalError

    client = RdbmsClient(
        RdbmsConnectionConfig(
            dbms="sqlite",
            database=str(tmp_path / "database.sqlite"),
            host=None,
            port=None,
            user=None,
            password=None,
            db_schema=None,
        ),
        task_id="bounded-fault",
    )
    with pytest.raises(OperationError) as caught:
        client.get("SELECT private_column FROM absent")
    error = caught.value
    assert isinstance(error.__cause__, OperationalError)
    assert isinstance(pickle.loads(pickle.dumps(error)).__cause__, OperationalError)
    normalize_error_cause_for_transport(error)
    assert isinstance(error.__cause__, ExternalFailureCause)
    assert error.__cause__.vendor_type == "sqlalchemy.exc.OperationalError"
    assert "private_column" not in str(error.__cause__)
    received = _receive(dryrun._WorkerFailure(message=str(error), fix_hint="Repair source.", error=error))
    assert type(received.error) is type(error)
    assert received.error.code is error.code and received.error.issue_code is error.issue_code
    assert isinstance(received.error.__cause__, ExternalFailureCause)
    client.engine.dispose()


def test_exporter_owned_transport_normalizer_preserves_native_cause_outside_child():
    from datamimic_ce.engine.io.api import normalize_exporter_error_cause_for_transport
    from datamimic_ce.engine.io.exporters.core.unified_buffered_exporter import ExportError
    from datamimic_ce.errors import ExternalFailureCause, IssueCode, export_config_error
    cause = ExportError("private-output-path")
    cause.__cause__ = OSError("private-filesystem-fact")
    error = export_config_error(code=IssueCode.EXPORT_FLUSH_FAILED, detail="ExportError")
    error.__cause__ = cause
    import pickle
    assert type(pickle.loads(pickle.dumps(error)).__cause__) is ExportError
    normalize_exporter_error_cause_for_transport(error)
    assert isinstance(error.__cause__, ExternalFailureCause)
    assert error.__cause__.vendor_type.endswith(".ExportError")
    assert error.__cause__.cause_types[-1] == "builtins.OSError"
    assert "private-" not in str(error.__cause__)
    received = _receive(dryrun._WorkerFailure(message=str(error), fix_hint="Repair output.", error=error))
    assert type(received.error) is type(error)
    assert received.error.issue_code is IssueCode.EXPORT_FLUSH_FAILED


def test_exporter_transport_facts_keep_nested_vendor_types():
    from datamimic_ce.engine.io.api import (
        normalize_error_cause_for_transport,
        normalize_exporter_error_cause_for_transport,
    )
    from datamimic_ce.engine.io.exporters.core.unified_buffered_exporter import ExportError
    from datamimic_ce.errors import ExternalFailureCause, IssueCode, export_config_error
    from sqlalchemy.exc import OperationalError

    cause = ExportError("output")
    cause.__cause__ = OperationalError("private-query", {}, OSError("private-driver-fact"))
    error = export_config_error(code=IssueCode.EXPORT_FLUSH_FAILED, detail="ExportError")
    error.__cause__ = cause
    normalize_exporter_error_cause_for_transport(error)
    normalize_error_cause_for_transport(error)
    assert isinstance(error.__cause__, ExternalFailureCause)
    assert error.__cause__.cause_types == (
        "datamimic_ce.engine.io.exporters.core.unified_buffered_exporter.ExportError",
        "sqlalchemy.exc.OperationalError",
    )
    assert "private-" not in str(error.__cause__)


@pytest.mark.parametrize(
    "accesses",
    [(("", 1),), (("file_csv", 0),), (("file_csv", -1),), (("file_csv", True),), ((1, 1),), (("file_csv", "1"),)],
)
def test_parent_revalidates_observed_source_access_fields(accesses):
    message = dryrun._WorkerSuccess(
        captured={"items": ({"id": 1},)},
        budgets=(_budget(),),
        smoke_diagnostics=(),
        smoke_export=SmokeExportCapture.not_requested(),
    )
    object.__setattr__(message, "source_accesses", accesses)
    assert _receive(message) is None
