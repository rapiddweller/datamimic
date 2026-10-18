"""Portable errors retain truthful identity across parsing and process boundaries."""

import logging
import multiprocessing
import pickle
from xml.etree.ElementTree import fromstring

import pytest
from pydantic import BaseModel, model_validator

from datamimic_ce.engine.dsl.parsers.flow.commands.echo_parser import EchoParser
from datamimic_ce.errors import (
    DescriptorLocation,
    ErrorCode,
    IssueCode,
    ParserValidationError,
    UserErrorBase,
    parser_validation_error,
    task_warning,
)
from datamimic_ce.errors.catalog import ISSUE_DEFINITIONS, IssueSeverity
from datamimic_ce.errors.formatters import issue_text


def _spawn_error(queue):
    try:
        raise ValueError("original failure")
    except ValueError as cause:
        error = parser_validation_error(
            code=IssueCode.PARSER_INVALID_TAG,
            expected="setup",
            actual="wrong",
            location=DescriptorLocation("wrong", descriptor_path="datamimic.xml"),
        )
        error.__cause__ = cause
        queue.put(error)


def test_factory_keeps_identity_location_and_cause_through_pickle_and_spawn():
    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    process = context.Process(target=_spawn_error, args=(queue,))
    process.start()
    error = queue.get(timeout=30)
    process.join(timeout=30)
    assert process.exitcode == 0
    assert type(error) is ParserValidationError
    assert isinstance(error, ValueError)
    assert error.code is ErrorCode.PARSER_VALIDATION
    assert error.issue_code is IssueCode.PARSER_INVALID_TAG
    assert error.location == DescriptorLocation("wrong", descriptor_path="datamimic.xml")
    assert type(error.__cause__) is ValueError
    assert str(error.__cause__) == "original failure"
    restored = pickle.loads(pickle.dumps(error))
    assert restored.__dict__ == error.__dict__
    assert str(restored.__cause__) == "original failure"
    queue.close()


def test_catalog_templates_reject_missing_and_extra_fields():
    assert "setup" in issue_text(IssueCode.PARSER_INVALID_TAG, expected="setup", actual="wrong")
    with pytest.raises(ValueError, match="missing="):
        issue_text(IssueCode.PARSER_INVALID_TAG, expected="setup")
    with pytest.raises(ValueError, match="extra="):
        issue_text(IssueCode.PARSER_INVALID_TAG, expected="setup", actual="wrong", extra=True)


def test_warning_codes_are_severity_checked_and_deduplicated(caplog, monkeypatch):
    logger = logging.getLogger("DATAMIMIC")
    monkeypatch.setattr(logger, "propagate", False)
    logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.WARNING, logger="DATAMIMIC"):
            task_warning(code=IssueCode.ECHO_PLACEHOLDER_UNRESOLVED, value="portable-unique", error_clause="")
            task_warning(code=IssueCode.ECHO_PLACEHOLDER_UNRESOLVED, value="portable-unique", error_clause="")
            task_warning(
                code=IssueCode.ECHO_PLACEHOLDER_UNRESOLVED, value="portable-unique", error_clause="", once=False
            )
    finally:
        logger.removeHandler(caplog.handler)
    assert sum("portable-unique" in record.message for record in caplog.records) == 2
    with pytest.raises(ValueError, match="WARNING"):
        task_warning(code=IssueCode.PARSER_INVALID_TAG, expected="setup", actual="wrong")
    with pytest.raises(ValueError, match="WARNING"):
        parser_validation_error(code=IssueCode.ECHO_PLACEHOLDER_UNRESOLVED, value="x", error_clause="")
    assert len({definition.code for definition in ISSUE_DEFINITIONS}) == len(ISSUE_DEFINITIONS)
    for definition in ISSUE_DEFINITIONS:
        assert definition.code.value.startswith("W") == (definition.severity is IssueSeverity.WARNING)


def test_parser_model_error_without_field_path_has_no_none_prefix():
    class RejectModel(BaseModel):
        @model_validator(mode="after")
        def reject(self):
            raise ValueError("root constraint violated")

    parser = EchoParser(fromstring("<echo/>"), {})
    with pytest.raises(ParserValidationError) as caught:
        parser.validate_attributes(RejectModel)
    assert isinstance(caught.value, UserErrorBase)
    assert caught.value.issue_code is IssueCode.PARSER_VALIDATION_FAILED
    assert "None:" not in str(caught.value)
    assert caught.value.location.element_tag == "echo"
    assert caught.value.__cause__ is not None


def test_parser_invalid_tag_uses_shared_factory():
    with pytest.raises(ParserValidationError) as caught:
        EchoParser(fromstring("<wrong/>"), {})
    assert caught.value.issue_code is IssueCode.PARSER_INVALID_TAG
    assert "[E011/I602]" in str(caught.value)


def test_expression_error_is_typed_and_keeps_original_cause():
    from datamimic_ce.engine.runtime.scripting.evaluation import evaluate_python
    from datamimic_ce.errors import TaskConfigError

    with pytest.raises(TaskConfigError) as caught:
        evaluate_python("missing_value + 1", {}, {})
    assert caught.value.issue_code is IssueCode.TASK_EXPRESSION_EVAL_FAILED
    assert type(caught.value.__cause__) is NameError
    assert "scope" in str(caught.value)


def test_generate_unknown_target_uses_catalog(tmp_path):
    from datamimic_ce.engine.runtime.api import run
    from datamimic_ce.engine.runtime.contracts import RunRequest
    from datamimic_ce.errors import ExportConfigError

    path = tmp_path / "datamimic.xml"
    path.write_text(
        '<setup rngSeed="7"><generate name="rows" count="1" target="MissingTarget">'
        '<key name="id" constant="1"/></generate></setup>'
    )
    with pytest.raises(ExportConfigError) as caught:
        run(RunRequest(descriptor_path=path, test_mode=True))
    assert caught.value.issue_code is IssueCode.EXPORT_TARGET_NOT_FOUND
    assert str(tmp_path) not in str(caught.value)


def test_datetime_invalid_weights_use_catalog():
    from datamimic_ce.domains.shared.literal_generators.temporal.datetime_generator import DateTimeGenerator
    from datamimic_ce.errors import GeneratorConfigError

    with pytest.raises(GeneratorConfigError) as caught:
        DateTimeGenerator(hour_weights=[1])
    assert caught.value.issue_code is IssueCode.DATETIME_WEIGHTS_LENGTH


def test_mongodb_selector_error_uses_normalized_facts():
    from datamimic_ce.engine.io.clients.mongodb_client import MongoDBClient
    from datamimic_ce.errors import InvalidSourceError

    client = object.__new__(MongoDBClient)
    with pytest.raises(InvalidSourceError) as caught:
        client._decompose_find_query('{find: "customers", filter: BROKEN}')
    assert caught.value.issue_code is IssueCode.SOURCE_MONGO_SELECTOR_INVALID
    assert caught.value.__cause__ is not None
    assert "BROKEN" not in str(caught.value)


def test_source_json_diagnostics_keep_logical_name_and_cause(tmp_path):
    from datamimic_ce.engine.io.files.readers import FileUtil
    from datamimic_ce.errors import InvalidSourceError

    path = tmp_path / "source.json"
    path.write_text("{malformed")
    with pytest.raises(InvalidSourceError) as caught:
        FileUtil.read_json(path)
    assert caught.value.issue_code is IssueCode.SOURCE_INVALID_JSON
    assert caught.value.__cause__ is not None
    assert "source.json" in str(caught.value)
    assert str(tmp_path) not in str(caught.value)


def test_converter_failure_retains_specific_type(tmp_path):
    from datamimic_ce.engine.runtime.api import run
    from datamimic_ce.engine.runtime.contracts import RunRequest
    from datamimic_ce.errors import DateTimeConversionError

    path = tmp_path / "datamimic.xml"
    path.write_text(
        '<setup rngSeed="7"><generate name="rows" count="1">'
        '<key name="bad" constant="text" inDateFormat="%Y"/></generate></setup>'
    )
    with pytest.raises(DateTimeConversionError) as caught:
        run(RunRequest(descriptor_path=path, test_mode=True))
    assert caught.value.code is ErrorCode.DATETIME_CONVERSION_FAILED
    assert caught.value.__cause__ is not None


def test_error_locations_do_not_publish_absolute_host_paths():
    location = DescriptorLocation("key", descriptor_path="/private/secret/task/datamimic.xml")
    error = parser_validation_error(
        code=IssueCode.PARSER_INVALID_TAG, expected="setup", actual="wrong", location=location
    )
    assert location.descriptor_path == "datamimic.xml"
    assert "/private/secret" not in str(error)
    assert "datamimic.xml" in str(error)


def test_domain_error_pickle_preserves_explicit_cause():
    from datamimic_ce.errors import DomainError, DomainErrorCode

    try:
        try:
            raise ValueError("domain cause")
        except ValueError as cause:
            raise DomainError(DomainErrorCode.INVALID_REQUEST, "bad input", None, "/field", "hash") from cause
    except DomainError as error:
        restored = pickle.loads(pickle.dumps(error))
    assert type(restored) is DomainError
    assert str(restored.__cause__) == "domain cause"


def test_catalog_rejects_mismatched_warning_severity():
    from datamimic_ce.errors.catalog import IssueDefinition

    with pytest.raises(ValueError, match="severity"):
        IssueDefinition(
            code=IssueCode.ECHO_PLACEHOLDER_UNRESOLVED,
            name="bad",
            title="bad",
            template="bad",
            cause="bad",
            resolution="bad",
        )


def test_every_transferred_issue_has_a_ce_caller_with_matching_template_fields():
    import ast
    from pathlib import Path

    from datamimic_ce.errors.catalog import get_issue_definition
    from datamimic_ce.errors.formatters import _template_fields

    root = Path(__file__).parents[2] / "datamimic_ce"
    seen = set()
    for path in root.rglob("*.py"):
        if "errors" in path.relative_to(root).parts:
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.Call):
                continue
            issue = next((keyword.value for keyword in node.keywords if keyword.arg == "code"), None)
            if not (
                isinstance(issue, ast.Attribute) and isinstance(issue.value, ast.Name) and issue.value.id == "IssueCode"
            ):
                continue
            code = IssueCode[issue.attr]
            seen.add(code)
            provided = {keyword.arg for keyword in node.keywords} - {
                "code",
                "ctx",
                "descriptor_name",
                "location",
                "guidance",
                "validation_errors",
                "once",
            }
            assert provided == _template_fields(get_issue_definition(code).template), (path, node.lineno, code)
    assert seen
    assert seen == set(IssueCode)


def test_sql_read_error_normalizes_vendor_details(tmp_path):
    from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
    from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig
    from datamimic_ce.errors import OperationError

    client = RdbmsClient(
        RdbmsConnectionConfig(
            dbms="sqlite",
            database=str(tmp_path / "test.db"),
            host=None,
            port=None,
            user=None,
            password=None,
            db_schema=None,
        ),
        task_id="portable-errors",
    )
    with pytest.raises(OperationError) as caught:
        client.get("SELECT secret_customer_value FROM no_such_table")
    assert caught.value.issue_code is IssueCode.OPERATION_EXECUTION_FAILED
    assert caught.value.__cause__ is not None
    assert "secret_customer_value" not in str(caught.value)
    assert str(tmp_path) not in str(caught.value)
    client.engine.dispose()


def test_mongo_driver_error_normalizes_vendor_details(monkeypatch):
    from pymongo.errors import OperationFailure

    from datamimic_ce.engine.io.clients.mongodb_client import MongoDBClient
    from datamimic_ce.engine.io.connection_config.mongodb_connection_config import MongoDBConnectionConfig
    from datamimic_ce.errors import OperationError

    class FailedConnection:
        def __enter__(self):
            raise OperationFailure("private credential material")

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(
        "datamimic_ce.engine.io.clients.mongodb_client.MongoClient", lambda **kwargs: FailedConnection()
    )
    client = MongoDBClient(MongoDBConnectionConfig(host="localhost", port=27017, database="test"))
    with pytest.raises(OperationError) as caught:
        client.get("find:'customers',filter:{}")
    assert caught.value.issue_code is IssueCode.OPERATION_EXECUTION_FAILED
    assert type(caught.value.__cause__) is OperationFailure
    assert "private credential material" not in str(caught.value)


def test_export_dispatch_keeps_specific_user_error_identity(monkeypatch):
    from datamimic_ce.engine.io.exporters.core.exporter_state_manager import ExporterStateManager
    from datamimic_ce.engine.io.exporters.diagnostics.test_result_exporter import TestResultExporter
    from datamimic_ce.engine.io.exporters.session import consume_exporters

    error = parser_validation_error(code=IssueCode.PARSER_INVALID_TAG, expected="key", actual="wrong")
    exporter = TestResultExporter()

    def fail(*args):
        raise error

    monkeypatch.setattr(exporter, "consume", fail)
    with pytest.raises(ParserValidationError) as caught:
        consume_exporters(("rows", []), [], "rows", [], [exporter], ExporterStateManager(1))
    assert caught.value is error


def test_runtime_descriptor_and_factory_entity_failures_are_coded(tmp_path):
    from datamimic_ce.engine.runtime.api import create_run_session
    from datamimic_ce.engine.runtime.contracts import FactoryConfig, RunRequest
    from datamimic_ce.errors import ParserValidationError, TaskConfigError

    with pytest.raises(ParserValidationError) as missing:
        create_run_session(RunRequest(descriptor_path=tmp_path / "absent.xml"))
    assert missing.value.issue_code is IssueCode.PARSER_DESCRIPTOR_NOT_FOUND
    descriptor = tmp_path / "model.xml"
    descriptor.write_text("<setup/>")
    with pytest.raises(TaskConfigError) as entity:
        create_run_session(RunRequest(descriptor_path=descriptor, factory_config=FactoryConfig("missing", 1))).execute()
    assert entity.value.issue_code is IssueCode.TASK_ENTITY_NOT_FOUND


def test_mongo_shape_errors_use_existing_selector_identity():
    from datamimic_ce.engine.io.clients.mongodb_client import MongoDBClient
    from datamimic_ce.engine.io.connection_config.mongodb_connection_config import MongoDBConnectionConfig
    from datamimic_ce.errors import InvalidSourceError

    client = MongoDBClient(MongoDBConnectionConfig(host="localhost", port=27017, database="test"))
    with pytest.raises(InvalidSourceError) as shape:
        client._decompose_find_query("find:'rows'")
    assert shape.value.issue_code is IssueCode.SOURCE_MONGO_SELECTOR_INVALID
    with pytest.raises(InvalidSourceError) as namespace:
        client.insert(" ", [], False)
    assert namespace.value.issue_code is IssueCode.SOURCE_MONGO_SELECTOR_INVALID


def test_buffered_finalize_failure_is_coded_and_keeps_specific_cause(monkeypatch):
    from datamimic_ce.engine.io.exporters import lifecycle
    from datamimic_ce.engine.io.exporters.core.unified_buffered_exporter import BufferFileError
    from datamimic_ce.errors import ExportConfigError

    class FailedExporter:
        def finalize_chunks(self, worker_id):
            raise BufferFileError("private path details")

    monkeypatch.setattr(lifecycle, "_buffered_exporters", lambda *args: [FailedExporter()])
    with pytest.raises(ExportConfigError) as caught:
        lifecycle.finalize_exporter_chunks(None, "rows", None, [], range(1))
    assert caught.value.issue_code is IssueCode.EXPORT_FLUSH_FAILED
    assert type(caught.value.__cause__) is BufferFileError
    assert "private path details" not in str(caught.value)


def test_multiprocessing_platform_guidance_uses_actual_ce_backends():
    definition = next(item for item in ISSUE_DEFINITIONS if item.code is IssueCode.TASK_MP_PLATFORM_UNSUPPORTED)
    assert definition.resolution == "Use multiprocessing or ray (or omit to use multiprocessing)."


def test_pickle_keeps_every_known_user_error_metadata_field():
    from datamimic_ce.errors.base import InvalidDatasetError, MissingMemstoreProductError

    errors = [
        InvalidDatasetError("dataset", dataset="ZZ"),
        MissingMemstoreProductError("missing", product_type="rows"),
        parser_validation_error(
            code=IssueCode.PARSER_VALIDATION_FAILED,
            details="missing name",
            validation_errors=({"loc": ("name",), "type": "missing", "msg": "required"},),
        ),
    ]
    for error in errors:
        error.location = DescriptorLocation("generate", descriptor_path="model.xml", line=2)
        error.__cause__ = ValueError("original")
        restored = pickle.loads(pickle.dumps(error))
        assert type(restored) is type(error)
        assert restored.__dict__ == error.__dict__
        assert type(restored.__cause__) is ValueError
        assert str(restored.__cause__) == "original"


@pytest.mark.parametrize("helper_name", ["tag_user_error", "ensure_user_error"])
@pytest.mark.parametrize("native", [ValueError("left", "right"), FileNotFoundError(2, "missing", "model.xml")])
def test_generic_user_wrapper_normalizes_one_message_and_keeps_native_cause(helper_name, native):
    from datamimic_ce.errors import ensure_user_error, tag_user_error
    from datamimic_ce.errors.base import UserRuntimeError, UserValueError

    helper = tag_user_error if helper_name == "tag_user_error" else ensure_user_error
    wrapped = helper(native)
    assert type(wrapped) is (UserValueError if isinstance(native, ValueError) else UserRuntimeError)
    assert wrapped.args == (str(native),)
    assert str(wrapped) == str(native)
    assert wrapped.__cause__ is native
    restored = pickle.loads(pickle.dumps(wrapped))
    assert type(restored) is type(wrapped)
    assert restored.args == wrapped.args
    assert type(restored.__cause__) is type(native)
    assert str(restored.__cause__) == str(native)


@pytest.mark.parametrize("helper_name", ["tag_user_error", "ensure_user_error"])
def test_user_wrapper_keeps_existing_typed_error_identity_and_metadata(helper_name):
    from datamimic_ce.errors import DomainError, DomainErrorCode, ensure_user_error, tag_user_error

    helper = tag_user_error if helper_name == "tag_user_error" else ensure_user_error
    typed = parser_validation_error(
        code=IssueCode.PARSER_INVALID_TAG,
        expected="setup",
        actual="wrong",
        location=DescriptorLocation("wrong", descriptor_path="model.xml"),
    )
    domain = DomainError(DomainErrorCode.INVALID_REQUEST, "invalid", "repair", "/field", "hash", {"x": 1})
    for error in (typed, domain):
        cause = ValueError("native")
        object.__setattr__(error, "__cause__", cause)
        assert helper(error) is error
        assert error.__cause__ is cause
    assert typed.issue_code is IssueCode.PARSER_INVALID_TAG
    assert typed.location.descriptor_path == "model.xml"
    assert domain.to_dict() == {
        "code": DomainErrorCode.INVALID_REQUEST.value,
        "message": "invalid",
        "hint": "repair",
        "path": "/field",
        "request_hash": "hash",
        "details": {"x": 1},
    }


def test_memstore_error_pickle_preserves_native_args_and_text_repeatedly():
    from datamimic_ce.engine.io.memstore import Memstore
    from datamimic_ce.errors import MissingMemstoreProductError

    with pytest.raises(MissingMemstoreProductError) as caught:
        Memstore("mem").get_data_by_type("missing")
    error = caught.value
    original_args = error.args
    original_text = str(error)
    original_cause_args = error.__cause__.args
    for _ in range(3):
        error = pickle.loads(pickle.dumps(error))
        assert type(error) is MissingMemstoreProductError
        assert isinstance(error, KeyError)
        assert error.args == original_args
        assert str(error) == original_text
        assert error.product_type == "missing"
        assert error.code is ErrorCode.INVALID_SOURCE
        assert type(error.__cause__) is KeyError
        assert error.__cause__.args == original_cause_args
