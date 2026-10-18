"""Portable errors cross real runtime and public output boundaries intact."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
import sqlalchemy

from datamimic_ce.engine.runtime.api import run
from datamimic_ce.engine.runtime.contracts import RunRequest
from datamimic_ce.errors import DomainError, InvalidLocaleError, OperationError, UserErrorBase
from datamimic_ce.errors.context.descriptor_identity import descriptor_scope, get_descriptor_name


def _run(tmp_path, xml):
    path = tmp_path / "model.xml"
    path.write_text(xml, encoding="utf-8")
    return run(RunRequest(descriptor_path=path, test_mode=True, task_id="error-boundary"))


@pytest.mark.parametrize(
    "code,error_type",
    [
        (
            "from datamimic_ce.domains.facade import generate_domain\n"
            'generate_domain({"domain":"address","version":"v1","count":-1})',
            DomainError,
        ),
        (
            "from datamimic_ce.domains.shared.use_cases.address_api import AddressRequest, generate\n"
            'generate(AddressRequest(locale="xx_XX", request_hash="runtime-test"))',
            InvalidLocaleError,
        ),
    ],
)
def test_domain_errors_keep_public_metadata_through_execute(tmp_path, code, error_type):
    with pytest.raises(error_type) as caught:
        _run(tmp_path, f'<setup><execute type="python">{code}</execute></setup>')
    error = caught.value
    assert type(error) is error_type
    assert error.path and error.request_hash and error.message and error.hint
    assert error.to_dict()["code"] == error.code.value
    assert get_descriptor_name() is None


def test_descriptor_scope_preserves_frozen_error_identity_and_nested_reset():
    from datamimic_ce.errors import DomainErrorCode

    error = DomainError(DomainErrorCode.INVALID_REQUEST, "bad", "repair", "/field", "hash")
    with descriptor_scope("outer.xml"):
        with pytest.raises(DomainError) as caught, descriptor_scope("inner.xml"):
            assert get_descriptor_name() == "inner.xml"
            raise error
        assert caught.value is error
        assert get_descriptor_name() == "outer.xml"
    assert get_descriptor_name() is None


@pytest.mark.parametrize("xml", ["<setup><generate></setup>", '<!DOCTYPE setup [<!ENTITY x "x">]><setup/>'])
def test_invalid_xml_is_a_portable_parser_error(tmp_path, xml):
    with pytest.raises(UserErrorBase) as caught:
        _run(tmp_path, xml)
    error = caught.value
    assert error.code.value == "E011"
    assert error.issue_code.value == "I610"
    assert error.location.descriptor_path == "model.xml"
    assert error.__cause__ is not None
    assert str(tmp_path) not in str(error)


@pytest.mark.parametrize(
    "xml,filename,content,cause_type",
    [
        ('<setup><variable name="v" source="source.csv" storage="data"/></setup>', "source.csv", b"x\n1\n", None),
        (
            '<setup><generate name="rows" source="source.dbunit.xml" sourceEntity="rows"/></setup>',
            "source.dbunit.xml",
            b"<oops/>",
            None,
        ),
        (
            '<setup><generate name="rows" count="1" source="source.json"/></setup>',
            "source.json",
            b"\xff",
            UnicodeDecodeError,
        ),
        ('<setup><execute type="python">int("not_a_number")</execute></setup>', None, None, ValueError),
    ],
)
def test_user_source_and_script_failures_are_portable(tmp_path, monkeypatch, xml, filename, content, cause_type):
    monkeypatch.chdir(tmp_path)
    if filename:
        (tmp_path / filename).write_bytes(content)
    with pytest.raises(UserErrorBase) as caught:
        _run(tmp_path, xml)
    assert caught.value.issue_code is not None
    assert str(tmp_path) not in str(caught.value)
    if cause_type:
        assert isinstance(caught.value.__cause__, cause_type)


def _sqlite_client(**options):
    from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
    from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig

    return RdbmsClient(
        RdbmsConnectionConfig(
            dbms="sqlite", database="audit", host=None, port=None, user=None, password=None, db_schema=None, **options
        ),
        task_id="errors",
    )


@pytest.mark.parametrize("method", ["get", "execute_sql_script"])
def test_sql_acquisition_failure_is_normalized(tmp_path, monkeypatch, method):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "db" / "audit.sqlite").mkdir(parents=True)
    client = _sqlite_client()
    try:
        with pytest.raises(OperationError) as caught:
            getattr(client, method)("select 1")
        assert caught.value.issue_code.value == "I901"
        assert isinstance(caught.value.__cause__, sqlalchemy.exc.OperationalError)
        assert "connection_failed" in str(caught.value)
        assert "14" in str(caught.value)
        assert str(tmp_path) not in str(caught.value)
    finally:
        if client.engine is not None:
            client.engine.dispose()


def test_sql_engine_configuration_is_normalized(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(UserErrorBase) as caught:
        _sqlite_client(encoding="bad").execute_sql_script("select 1")
    assert caught.value.code.value == "E012"
    assert isinstance(caught.value.__cause__, TypeError)


def test_sql_script_rollback_is_preserved(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    client = _sqlite_client()
    try:
        client.execute_sql_script("CREATE TABLE entries (id INTEGER)")
        with pytest.raises(OperationError):
            client.execute_sql_script("INSERT INTO entries VALUES (1); SELECT * FROM missing_table")
        assert client.get("SELECT * FROM entries") == []
    finally:
        if client.engine is not None:
            client.engine.dispose()


def test_cli_user_failure_does_not_publish_native_sql_or_traceback(tmp_path):
    sentinel = "AUDIT_SYNTHETIC_SECRET_6a8e"
    path = tmp_path / "model.xml"
    path.write_text(
        '<setup><database id="db" dbms="sqlite" database="audit"/>'
        '<execute target="db" type="sql">SELECT \'{secret_value}\' FROM missing_table</execute></setup>'
    )
    root = Path(__file__).parents[2]
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "datamimic_ce.interfaces.cli",
            "run",
            str(path),
            "--param-env",
            "secret_value=AUDIT_ERROR_TOKEN",
            "--test-mode",
        ],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(root), "AUDIT_ERROR_TOKEN": sentinel, "NO_COLOR": "1"},
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 1
    assert "E014/I901" in output
    assert sentinel not in output
    assert "Traceback" not in output


def test_bounded_error_keeps_catalog_remediation_and_logical_field(tmp_path):
    from datamimic_ce.authoring import create_authoring_application
    from datamimic_ce.authoring.domain.requests import RunRequest as AuthoringRunRequest

    result = create_authoring_application(tmp_path).dry_run(
        AuthoringRunRequest(
            xml='<setup rngSeed="7"><generate name="rows" count="1"><key name="x" script="1/0"/></generate></setup>'
        )
    )
    assert not result.ok
    diagnostic = result.diagnostics[0]
    assert diagnostic.ce_error.issue_code.value == "I832"
    assert "scope" in diagnostic.remediation
    assert "key" in diagnostic.path
    assert "script" in diagnostic.path
    assert str(tmp_path) not in diagnostic.model_dump_json()


@pytest.mark.parametrize(
    "code,category",
    [
        ("42P01", "table_not_found"),
        ("42703", "column_not_found"),
        ("3F000", "schema_not_found"),
        ("42501", "permission_denied"),
        ("42601", "syntax_error"),
        ("08006", "connection_failed"),
    ],
)
def test_sql_native_codes_keep_normalized_facts_without_statement_data(monkeypatch, code, category):
    class NativePgError(Exception):
        pgcode = code

    original = NativePgError("private vendor statement detail")
    failure = sqlalchemy.exc.ProgrammingError("SELECT private_value", {}, original)
    client = _sqlite_client()

    def fail():
        raise failure

    monkeypatch.setattr(client, "_create_engine", fail)
    with pytest.raises(OperationError) as caught:
        client.get("SELECT private_value")
    assert category in str(caught.value)
    assert code in str(caught.value)
    assert "private" not in str(caught.value)
    assert caught.value.__cause__ is failure


def test_domain_error_through_key_expression_keeps_domain_contract(tmp_path):
    xml = """<setup><execute type="python">from datamimic_ce.domains.facade import generate_domain</execute>
    <generate name="rows" count="1">
      <key name="x" script="generate_domain({'domain':'address','version':'v1','count':-1})"/>
    </generate></setup>"""
    with pytest.raises(DomainError) as caught:
        _run(tmp_path, xml)
    assert type(caught.value) is DomainError
    assert caught.value.path and caught.value.request_hash


def test_mysql_driver_error_uses_declared_connector_native_facts(monkeypatch):
    from mysql.connector.errors import ProgrammingError

    client = _sqlite_client()
    failure = sqlalchemy.exc.ProgrammingError(
        "SELECT private_value", {}, ProgrammingError("private detail", errno=1146, sqlstate="42S02")
    )

    def fail():
        raise failure

    monkeypatch.setattr(client, "_create_engine", fail)
    with pytest.raises(OperationError) as caught:
        client.get("SELECT private_value")
    assert "1146" in str(caught.value)
    assert "table_not_found" in str(caught.value)
    assert "private" not in str(caught.value)


def test_sqlstate_is_used_when_legacy_pgcode_is_empty(monkeypatch):
    class NativeError(Exception):
        pgcode = None
        sqlstate = "42703"

    client = _sqlite_client()
    failure = sqlalchemy.exc.ProgrammingError("SELECT private_value", {}, NativeError("private detail"))

    def fail():
        raise failure

    monkeypatch.setattr(client, "_create_engine", fail)
    with pytest.raises(OperationError) as caught:
        client.get("SELECT private_value")
    assert "42703" in str(caught.value)
    assert "column_not_found" in str(caught.value)


@pytest.mark.parametrize("report_logging", [False, True])
def test_generation_timer_preserves_frozen_domain_error(report_logging):
    from datamimic_ce.engine.runtime.logging import gen_timer
    from datamimic_ce.errors import DomainErrorCode

    error = DomainError(DomainErrorCode.INVALID_REQUEST, "bad", "repair", "/field", "hash")
    with pytest.raises(DomainError) as caught, gen_timer("generate", report_logging, "rows") as result:
        result["records_count"] = 1
        raise error
    assert caught.value is error
    assert result == {"records_count": 1}


def test_unexpected_python_programming_error_keeps_native_type(tmp_path):
    with pytest.raises(RuntimeError, match="unexpected programming failure"):
        _run(
            tmp_path,
            '<setup><execute type="python">raise RuntimeError("unexpected programming failure")</execute></setup>',
        )


@pytest.mark.parametrize("locale", [False, True], ids=["domain", "locale"])
def test_domain_failure_survives_real_bounded_child(tmp_path, monkeypatch, locale):
    from datamimic_ce.authoring import create_authoring_application
    from datamimic_ce.authoring.adapters import dryrun
    from datamimic_ce.authoring.domain.requests import RunRequest as AuthoringRunRequest
    from datamimic_ce.domains.facade import generate_domain
    from datamimic_ce.domains.shared.use_cases.address_api import AddressRequest
    from datamimic_ce.domains.shared.use_cases.address_api import generate as generate_address
    from datamimic_ce.errors import ExternalFailureCause

    decoded = []
    original = dryrun._decode_worker_message

    def record(*args, **kwargs):
        message = original(*args, **kwargs)
        decoded.append(message)
        return message

    monkeypatch.setattr(dryrun, "_decode_worker_message", record)
    if locale:
        code = (
            "from datamimic_ce.domains.shared.use_cases.address_api import AddressRequest, generate\n"
            'generate(AddressRequest(locale="xx_XX"))'
        )
        with pytest.raises(InvalidLocaleError) as expected:
            generate_address(AddressRequest(locale="xx_XX"))
    else:
        code = (
            "from datamimic_ce.domains.facade import generate_domain\n"
            'generate_domain({"domain":"address","version":"v1","count":-1})'
        )
        with pytest.raises(DomainError) as expected:
            generate_domain({"domain": "address", "version": "v1", "count": -1})
    result = create_authoring_application(tmp_path).run(
        AuthoringRunRequest(xml=f'<setup><execute type="python">{code}</execute></setup>', allow_side_effects=True)
    )
    assert not result.ok
    assert result.diagnostics[0].remediation == expected.value.hint
    assert len(decoded) == 1
    assert decoded[0].error.to_dict() == expected.value.to_dict()
    if locale:
        assert result.diagnostics[0].ce_error.error_code.value == "E002"
        assert isinstance(decoded[0].error.__cause__, ExternalFailureCause)
        assert decoded[0].error.__cause__.cause_types == (
            "datamimic_ce.domains.shared.datasets.locales.UnsupportedLocaleDatasetError",
        )
        assert type(expected.value.__cause__).__name__ == "UnsupportedLocaleDatasetError"


def test_actual_locale_error_pickle_preserves_native_cause():
    import pickle

    from datamimic_ce.domains.shared.datasets.locales import UnsupportedLocaleDatasetError
    from datamimic_ce.domains.shared.use_cases.address_api import AddressRequest
    from datamimic_ce.domains.shared.use_cases.address_api import generate as generate_address

    with pytest.raises(InvalidLocaleError) as caught:
        generate_address(AddressRequest(locale="xx_XX", request_hash="locale-pickle"))
    native = caught.value.__cause__
    assert isinstance(native, UnsupportedLocaleDatasetError)
    restored = pickle.loads(pickle.dumps(caught.value))
    assert restored.to_dict() == caught.value.to_dict()
    assert type(restored.__cause__) is type(native)
    assert restored.__cause__.__dict__ == native.__dict__
    assert str(restored.__cause__) == str(native)


def test_actual_bounded_sql_error_keeps_safe_portable_identity(tmp_path):
    from datamimic_ce.authoring import create_authoring_application
    from datamimic_ce.authoring.domain.requests import RunRequest as AuthoringRunRequest

    xml = (
        '<setup><database id="db" dbms="sqlite" database="audit"/>'
        '<execute target="db" type="sql">SELECT \'synthetic_private_value\' FROM missing_table</execute></setup>'
    )
    result = create_authoring_application(tmp_path).run(AuthoringRunRequest(xml=xml, allow_side_effects=True))
    assert not result.ok
    assert result.diagnostics[0].code.value == "child_execution"
    assert result.diagnostics[0].ce_error.error_code.value == "E014"
    assert result.diagnostics[0].ce_error.issue_code.value == "I901"
    assert "synthetic_private_value" not in result.model_dump_json()


def test_missing_descriptor_preserves_native_catch_and_portable_identity(tmp_path):
    import pickle

    from datamimic_ce.engine.dsl.api import DescriptorParser
    from datamimic_ce.engine.io.api import load_connection_profile
    from datamimic_ce.errors import ParserValidationError

    with pytest.raises(FileNotFoundError, match="missing.xml") as caught:
        DescriptorParser.parse(tmp_path / "missing.xml", None, "production", profile_loader=load_connection_profile)
    error = caught.value
    assert isinstance(error, ParserValidationError)
    assert error.code.value == "E011"
    assert error.issue_code.value == "I609"
    assert error.location.descriptor_path == "missing.xml"
    assert isinstance(error.__cause__, FileNotFoundError)
    assert str(tmp_path) not in str(error)
    restored = pickle.loads(pickle.dumps(error))
    assert type(restored) is type(error)
    assert str(restored) == str(error)
    assert restored.__dict__ == error.__dict__
    assert type(restored.__cause__) is FileNotFoundError


def test_missing_static_properties_crosses_real_bounded_child(tmp_path):
    from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
    from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
    from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest

    result = CeBoundedExecutor(AuthoringWorkspaceContext(tmp_path)).execute(
        BoundedExecutionRequest(xml='<setup><include uri="missing.properties"/></setup>')
    )
    assert not result.ok
    assert result.diagnostics[0].code.value == "child_execution"
    assert result.diagnostics[0].ce_error.error_code.value == "E008"
    assert result.diagnostics[0].ce_error.issue_code.value == "I201"
    assert result.diagnostics[0].path[-2:] == ("include", "uri")
    assert str(tmp_path) not in result.diagnostics[0].model_dump_json()


def test_evaluated_unknown_mime_does_not_publish_runtime_value(tmp_path):
    sentinel = "AUDIT_MIME_SECRET_d2e4"
    path = tmp_path / "model.xml"
    path.write_text(
        '<setup><generate name="rows" count="1">'
        '<key name="payload" type="binary" mimeType="{mime}"/></generate></setup>'
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "datamimic_ce.interfaces.cli",
            "run",
            str(path),
            "--param-env",
            "mime=AUDIT_MIME_VALUE",
            "--test-mode",
        ],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).parents[2]), "AUDIT_MIME_VALUE": sentinel, "NO_COLOR": "1"},
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 1
    assert sentinel not in output
    assert "E009" in output
    assert "Supported" in output


@pytest.mark.parametrize(
    "declaration",
    [
        "IntegerGenerator(min='{secret}', max=5)",
        "StringGenerator(min_len='{secret}', max_len=5)",
        "DateTimeGenerator(min='{secret}')",
        "IntegerGenerator(min=int('{secret}'), max=5)",
        "{secret}",
    ],
)
def test_resolved_generator_native_failure_does_not_publish_parameters(tmp_path, declaration):
    sentinel = "AUDIT_GENERATOR_SECRET_efa1"
    path = tmp_path / "model.xml"
    path.write_text(
        '<setup><generate name="rows" count="1"><key name="value" generator="{declaration}"/></generate></setup>'
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "datamimic_ce.interfaces.cli",
            "run",
            str(path),
            "--param-env",
            "declaration=AUDIT_GENERATOR_DECLARATION",
            "--test-mode",
        ],
        cwd=tmp_path,
        env={
            **os.environ,
            "PYTHONPATH": str(Path(__file__).parents[2]),
            "AUDIT_GENERATOR_DECLARATION": declaration.format(secret=sentinel),
            "NO_COLOR": "1",
        },
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 1
    assert sentinel not in output
    assert "E009" in output or "E013" in output


def test_binary_constructor_reason_survives_actual_bounded_child(tmp_path):
    from datamimic_ce.authoring import create_authoring_application
    from datamimic_ce.authoring.domain.requests import RunRequest as AuthoringRunRequest

    result = create_authoring_application(tmp_path).dry_run(
        AuthoringRunRequest(
            xml=(
                '<setup><generate name="rows" count="1">'
                '<key name="payload" type="binary" mimeType="application/unknown"/></generate></setup>'
            )
        )
    )
    assert not result.ok
    assert result.diagnostics[0].ce_error.error_code.value == "E009"
    assert "Supported:" in result.diagnostics[0].message
    assert "generator parameters" in result.diagnostics[0].remediation
    assert "application/unknown" not in result.model_dump_json()


def test_substring_type_policy_never_renders_rejected_value():
    from datamimic_ce.domains.shared.converters.text.substring_converter import SubstringConverter
    from datamimic_ce.errors import ErrorCode, IssueCode, TaskConfigError

    class PrivateValue:
        def __str__(self):
            raise AssertionError("Rejected data must not be rendered")

        def __repr__(self):
            raise AssertionError("Rejected data must not be rendered")

    with pytest.raises(TaskConfigError, match="Substring.*string") as caught:
        SubstringConverter(1).convert(PrivateValue())
    assert isinstance(caught.value, ValueError)
    assert caught.value.code is ErrorCode.TASK_CONFIG
    assert caught.value.issue_code is IssueCode.TASK_DATATYPE_INVALID
    assert "PrivateValue" in str(caught.value)
    assert caught.value.__cause__ is None


def test_short_hash_key_is_typed_policy_without_key_or_salt_material():
    from datamimic_ce.domains.shared.converters.privacy.hash_converter import HashConverter
    from datamimic_ce.errors import ErrorCode, IssueCode, TaskConfigError

    sentinel = "HASH_PRIVATE_KEY_SENTINEL"
    with pytest.raises(TaskConfigError, match="at least 32 bytes") as caught:
        HashConverter("sha256", "hex", key=sentinel.encode(), salt=sentinel)
    assert isinstance(caught.value, ValueError)
    assert caught.value.code is ErrorCode.TASK_CONFIG
    assert caught.value.issue_code is IssueCode.TASK_CONVERTER_FAILED
    assert sentinel not in str(caught.value)
    assert caught.value.__cause__ is None


@pytest.mark.parametrize(
    "attributes,declaration",
    [
        ('constant="hello" converter="{declaration}"', "Substring('{sentinel}')"),
        ('constant="hello" converter="{declaration}"', "{sentinel}"),
        ('constant="hello" converter="{declaration}"', "Substring(1) and '{sentinel}'"),
        ('script="{declaration}"', "int('{sentinel}')"),
    ],
)
def test_resolved_converter_and_script_diagnostics_keep_parameter_private(tmp_path, attributes, declaration):
    sentinel = "AUDIT_CALLER_PRIVATE_c92a"
    path = tmp_path / "model.xml"
    path.write_text(f'<setup><generate name="rows" count="1"><key name="value" {attributes}/></generate></setup>')
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "datamimic_ce.interfaces.cli",
            "run",
            str(path),
            "--param-env",
            "declaration=AUDIT_DECLARATION",
        ],
        env={**os.environ, "AUDIT_DECLARATION": declaration.format(sentinel=sentinel)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 1
    assert sentinel not in completed.stdout + completed.stderr


@pytest.mark.parametrize(
    "body,expression,identity",
    [
        ('<generate name="rows" count="1"><array name="v" script="{expr}"/></generate>', "'{sentinel}'", "E013/I806"),
        (
            '<generate name="rows" count="1"><array name="v" script="{expr}"/></generate>',
            "[{{'{sentinel}': 1}}]",
            "E013/I804",
        ),
        (
            '<generate name="rows" count="1"><array name="v" script="{expr}"/></generate>',
            "['{sentinel}', 1]",
            "E013/I805",
        ),
        (
            '<generate name="rows" count="1"><nestedKey name="v" script="{expr}"/></generate>',
            "int('{sentinel}')",
            "E013/I832",
        ),
        (
            '<generate name="rows" count="1"><nestedKey name="v" script="{expr}"/></generate>',
            "'{sentinel}'",
            "E013/I815",
        ),
        (
            '<generate name="rows" count="1">'
            '<key name="v" script="os.environ[\'AUDIT_CALLER_SECRET\']"/><assert condition="False"/></generate>',
            "None",
            "E013/I895",
        ),
        ('<generate name="rows" count="1"><assert condition="{expr}"/></generate>', "int('{sentinel}')", "E013/I832"),
        (
            '<generate name="rows" count="{os.environ[\'AUDIT_CALLER_SECRET\']}">'
            '<key name="v" constant="ok"/></generate>',
            "None",
            "E013/I832",
        ),
        (
            '<generate name="rows" count="1"><key name="v" constant="ok" condition="{expr}"/></generate>',
            "'{sentinel}'",
            "E010/I507",
        ),
        ('<execute type="python" script="{expr}"/>', "len('{sentinel}')", "E013/I832"),
        (
            '<generate name="rows" count="1"><while condition="{expr}" maxIterations="1">'
            '<key name="v" constant="ok"/></while></generate>',
            "bool('{sentinel}')",
            "E013/I911",
        ),
        ('<variable name="v" entity="{expr}"/>', "{sentinel}", "E004"),
        ("<execute type=\"python\">import os\nint(os.environ['AUDIT_CALLER_SECRET'])</execute>", "None", "E013/I832"),
        ("<execute type=\"python\">import os\neval(os.environ['AUDIT_CALLER_SECRET'])</execute>", "None", "E013/I832"),
        ('<execute type="python">{sentinel}=1\nglobal {sentinel}</execute>', "None", "E013/I832"),
    ],
)
def test_expression_consumers_keep_runtime_values_private(tmp_path, body, expression, identity):
    sentinel = "AUDIT_ALL_CALLERS_PRIVATE_b4d7"
    path = tmp_path / "model.xml"
    path.write_text('<setup rngSeed="7">' + body.replace("{sentinel}", sentinel) + "</setup>")
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "datamimic_ce.interfaces.cli",
            "run",
            str(path),
            "--param-env",
            "expr=AUDIT_CALLER_EXPRESSION",
            "--test-mode",
        ],
        env={
            **os.environ,
            "AUDIT_CALLER_EXPRESSION": expression.format(sentinel=sentinel),
            "AUDIT_CALLER_SECRET": sentinel,
        },
        capture_output=True,
        text=True,
        check=False,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 1
    assert identity in output
    assert sentinel not in output
    assert "Traceback" not in output


def test_literal_descriptor_words_do_not_suppress_runtime_context(tmp_path):
    with pytest.raises(UserErrorBase) as caught:
        _run(
            tmp_path,
            '<setup><generate name="rows" count="1">'
            '<key name="value" values="descriptor &apos;source&apos;"/></generate></setup>',
        )
    assert "in descriptor 'model.xml'" in str(caught.value)


@pytest.mark.parametrize("cause", ["Input value is empty", "Date input is empty", "ValueError"])
def test_empty_date_guidance_uses_the_fact_not_cause_wording(cause):
    from datamimic_ce.errors.catalog import GUIDANCE_EMPTY_VALUE
    from datamimic_ce.errors.factory import datetime_conversion_error

    error = datetime_conversion_error(
        element_tag="key",
        name="date",
        in_fmt="%Y",
        out_fmt=None,
        cause=cause,
        input_empty=True,
    )
    assert GUIDANCE_EMPTY_VALUE in str(error)


def test_empty_date_runtime_supplies_guidance_fact(tmp_path):
    from datamimic_ce.errors import DateTimeConversionError
    from datamimic_ce.errors.catalog import GUIDANCE_EMPTY_VALUE

    with pytest.raises(DateTimeConversionError) as caught:
        _run(
            tmp_path,
            '<setup><generate name="rows" count="1">'
            '<key name="date" constant=" " inDateFormat="%Y"/></generate></setup>',
        )
    assert GUIDANCE_EMPTY_VALUE in str(caught.value)
    assert caught.value.__cause__ is not None


def test_descriptor_hint_deduplication_uses_only_the_actual_suffix():
    from datamimic_ce.errors import descriptor_hint_if_missing
    from datamimic_ce.errors.factory import _append_descriptor_hint

    hint = " in descriptor 'model.xml'"
    assert descriptor_hint_if_missing("bad descriptor 'source'", None, "model.xml") == hint
    assert descriptor_hint_if_missing("bad" + hint, None, "model.xml") == ""
    assert _append_descriptor_hint("bad" + hint, None, "model.xml") == "bad" + hint


def test_date_guidance_is_not_inferred_from_untrusted_cause_text():
    from datamimic_ce.errors import datetime_conversion_error
    from datamimic_ce.errors.catalog import GUIDANCE_EMPTY_VALUE

    error = datetime_conversion_error(
        element_tag="key",
        name="date",
        in_fmt="%Y",
        out_fmt=None,
        cause="Input value is empty",
        input_empty=False,
    )
    assert GUIDANCE_EMPTY_VALUE not in str(error)


@pytest.mark.parametrize("descriptor_name", [None, "actual.xml"])
@pytest.mark.parametrize("cause", ["boom.", "upstream descriptor 'source' failed."])
def test_script_error_factory_preserves_cause_and_owns_descriptor(descriptor_name, cause):
    from datamimic_ce.errors import IssueCode, task_config_error

    with descriptor_scope(None):
        error = task_config_error(
            code=IssueCode.TASK_SCRIPT_ERROR,
            descriptor_name=descriptor_name,
            element_label="<key> 'amount'",
            descriptor=" in descriptor 'legacy.xml'",
            error=cause,
        )
    assert str(error) == (
        "[E013/I812] Invalid task configuration: Script error in <key> 'amount'"
        f" in descriptor '{descriptor_name or 'legacy.xml'}': {cause}"
    )
