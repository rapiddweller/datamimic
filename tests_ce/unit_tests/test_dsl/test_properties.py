from pathlib import Path
from typing import Literal
from xml.etree import ElementTree as ET

import pytest

from datamimic_ce.engine.dsl.api import Statement, parse_properties
from datamimic_ce.engine.dsl.model.setup.include_model import IncludeModel
from datamimic_ce.engine.dsl.parsers.base import dispatch
from datamimic_ce.engine.dsl.parsers.base.client_config import fulfill_credentials
from datamimic_ce.engine.dsl.parsers.document.descriptor_parser import DescriptorParser
from datamimic_ce.engine.dsl.parsers.generation.generate_parser import GenerateParser
from datamimic_ce.engine.dsl.parsers.input import properties as property_input
from datamimic_ce.engine.dsl.statements.setup.include_statement import IncludeStatement
from datamimic_ce.engine.dsl.statements.setup.mongodb_statement import MongoDBStatement
from datamimic_ce.engine.io.api import load_connection_profile
from datamimic_ce.engine.io.files.api import FileUtil
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.tasks.base.task import SetupSubTask
from datamimic_ce.engine.runtime.tasks.setup.include_task import IncludeTask


def test_parse_properties_preserves_comment_and_value_semantics(tmp_path: Path) -> None:
    properties_file = tmp_path / "test.properties"
    properties_file.write_text("  # comment\n\n key = value=tail \n", encoding="utf-8")

    assert parse_properties(properties_file) == {"key": "value=tail"}
    assert FileUtil.parse_properties(properties_file) == {"key": "value=tail"}


def test_parse_properties_preserves_missing_file_error(tmp_path: Path) -> None:
    properties_file = tmp_path / "missing.properties"

    with pytest.raises(FileNotFoundError, match="Property file not found"):
        parse_properties(properties_file)


def test_parse_properties_caches_lines_by_path_and_returns_fresh_dict(tmp_path: Path) -> None:
    properties_file = tmp_path / "cached.properties"
    properties_file.write_text("key=first\n", encoding="utf-8")

    first = parse_properties(properties_file)
    properties_file.write_text("key=second\n", encoding="utf-8")
    second = parse_properties(properties_file)

    assert first == {"key": "first"}
    assert second == {"key": "first"}
    assert first is not second


@pytest.mark.parametrize(
    ("runtime_environment", "environment_name"),
    [("development", "local"), ("production", "environment")],
)
def test_credentials_use_runtime_default_environment(
    tmp_path: Path,
    runtime_environment: Literal["development", "production"],
    environment_name: str,
) -> None:
    config_dir = tmp_path / "conf"
    config_dir.mkdir()
    (config_dir / f"{environment_name}.env.properties").write_text(
        "store.db.url=jdbc:test\n", encoding="utf-8"
    )

    credentials = fulfill_credentials(
        descriptor_dir=tmp_path,
        descriptor_attr={"id": "store"},
        env_props=None,
        system_type="db",
        runtime_environment=runtime_environment,
        profile_loader=load_connection_profile,
    )

    assert credentials["url"] == "jdbc:test"


def test_descriptor_parser_propagates_runtime_environment(tmp_path: Path) -> None:
    config_dir = tmp_path / "conf"
    config_dir.mkdir()
    (config_dir / "local.env.properties").write_text(
        "mongodb.mongo.host=localhost\nmongodb.mongo.port=47017\nmongodb.mongo.database=datamimic\n",
        encoding="utf-8",
    )
    descriptor = tmp_path / "descriptor.xml"
    descriptor.write_text('<setup><mongodb id="mongodb"/></setup>', encoding="utf-8")

    setup = DescriptorParser.parse(descriptor, None, "development", profile_loader=load_connection_profile)

    mongodb = setup.sub_statements[0]
    assert isinstance(mongodb, MongoDBStatement)
    assert mongodb.model.host == "localhost"


def test_credentials_merge_descriptor_then_truthy_platform_then_descriptor_profile(tmp_path: Path) -> None:
    config_dir = tmp_path / "conf"
    config_dir.mkdir()
    (config_dir / "environment.env.properties").write_text(
        "store.db.user=profile-user\nstore.db.password=profile-password\n",
        encoding="utf-8",
    )
    platform_props = {"store.db.user": "platform-user", "store.db.url": "platform-url"}

    credentials = fulfill_credentials(
        descriptor_dir=tmp_path,
        descriptor_attr={"id": "store", "url": "descriptor-url", "user": "descriptor-user"},
        env_props=platform_props,
        system_type="db",
        runtime_environment="production",
        profile_loader=load_connection_profile,
    )

    assert credentials["url"] == "platform-url"
    assert credentials["user"] == "profile-user"
    assert credentials["password"] == "profile-password"
    assert platform_props["store.db.user"] == "profile-user"
    assert platform_props["store.db.password"] == "profile-password"


def test_empty_platform_properties_do_not_alias_or_mutate_when_profile_is_loaded(tmp_path: Path) -> None:
    config_dir = tmp_path / "conf"
    config_dir.mkdir()
    (config_dir / "environment.env.properties").write_text("store.db.user=profile-user\n", encoding="utf-8")
    platform_props: dict[str, str] = {}

    credentials = fulfill_credentials(
        descriptor_dir=tmp_path,
        descriptor_attr={"id": "store"},
        env_props=platform_props,
        system_type="db",
        runtime_environment="production",
        profile_loader=load_connection_profile,
    )

    assert credentials["user"] == "profile-user"
    assert platform_props == {}


def test_credentials_prefer_the_descriptor_profile_before_the_current_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    descriptor_dir = tmp_path / "descriptor"
    (descriptor_dir / "conf").mkdir(parents=True)
    (descriptor_dir / "conf/environment.env.properties").write_text("store.db.user=descriptor-user\n", encoding="utf-8")
    current_dir = tmp_path / "current"
    current_dir.mkdir()
    (current_dir / "environment.env.properties").write_text("store.db.user=current-user\n", encoding="utf-8")
    monkeypatch.chdir(current_dir)

    credentials = fulfill_credentials(
        descriptor_dir=descriptor_dir,
        descriptor_attr={"id": "store"},
        env_props=None,
        system_type="db",
        runtime_environment="production",
        profile_loader=load_connection_profile,
    )

    assert credentials["user"] == "descriptor-user"


def test_credentials_fall_back_to_the_current_directory_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    current_dir = tmp_path / "current"
    current_dir.mkdir()
    (current_dir / "environment.env.properties").write_text("store.db.user=current-user\n", encoding="utf-8")
    monkeypatch.chdir(current_dir)
    monkeypatch.setattr(property_input, "_PROPERTY_LINES", {})

    credentials = fulfill_credentials(
        descriptor_dir=tmp_path / "descriptor-without-conf",
        descriptor_attr={"id": "store"},
        env_props=None,
        system_type="db",
        runtime_environment="production",
        profile_loader=load_connection_profile,
    )

    assert credentials["user"] == "current-user"


def test_credentials_fall_back_to_the_user_profile_after_current_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    current_dir = tmp_path / "current"
    current_dir.mkdir()
    home_dir = tmp_path / "home"
    profile_dir = home_dir / "datamimic"
    profile_dir.mkdir(parents=True)
    (profile_dir / "environment.env.properties").write_text("store.db.user=home-user\n", encoding="utf-8")
    monkeypatch.chdir(current_dir)
    monkeypatch.setattr("os.path.expanduser", lambda _path: str(home_dir))
    monkeypatch.setattr(property_input, "_PROPERTY_LINES", {})

    credentials = fulfill_credentials(
        descriptor_dir=tmp_path / "descriptor-without-conf",
        descriptor_attr={"id": "store"},
        env_props=None,
        system_type="db",
        runtime_environment="production",
        profile_loader=load_connection_profile,
    )

    assert credentials["user"] == "home-user"


def test_credentials_search_descriptor_then_current_directory_then_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    descriptor_dir = tmp_path / "descriptor"
    (descriptor_dir / "conf").mkdir(parents=True)
    (descriptor_dir / "conf/environment.env.properties").write_text("store.db.user=descriptor-user\n", encoding="utf-8")
    current_dir = tmp_path / "current"
    current_dir.mkdir()
    (current_dir / "environment.env.properties").write_text("store.db.user=current-user\n", encoding="utf-8")
    home_dir = tmp_path / "home"
    profile_dir = home_dir / "datamimic"
    profile_dir.mkdir(parents=True)
    (profile_dir / "environment.env.properties").write_text("store.db.user=home-user\n", encoding="utf-8")
    monkeypatch.chdir(current_dir)
    monkeypatch.setattr("os.path.expanduser", lambda _path: str(home_dir))

    credentials = fulfill_credentials(
        descriptor_dir=descriptor_dir,
        descriptor_attr={"id": "store"},
        env_props=None,
        system_type="db",
        runtime_environment="production",
        profile_loader=load_connection_profile,
    )

    assert credentials["user"] == "descriptor-user"


def test_credentials_without_any_profile_keep_descriptor_attributes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    current_dir = tmp_path / "current"
    current_dir.mkdir()
    monkeypatch.chdir(current_dir)
    monkeypatch.setattr("os.path.expanduser", lambda _path: str(tmp_path / "missing-home"))
    monkeypatch.setattr(property_input, "_PROPERTY_LINES", {})

    credentials = fulfill_credentials(
        descriptor_dir=tmp_path / "descriptor-without-conf",
        descriptor_attr={"id": "store", "user": "descriptor-user"},
        env_props=None,
        system_type="db",
        runtime_environment="production",
        profile_loader=load_connection_profile,
    )

    assert credentials == {"id": "store", "user": "descriptor-user"}


def test_credentials_do_not_suppress_profile_permission_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def unreadable_profile(_path: Path, _environment: str) -> dict[str, str]:
        raise PermissionError("profile is unreadable")

    with pytest.raises(PermissionError, match="profile is unreadable"):
        fulfill_credentials(
            descriptor_dir=tmp_path,
            descriptor_attr={"id": "store"},
            env_props=None,
            system_type="db",
            runtime_environment="production",
            profile_loader=unreadable_profile,
        )


@pytest.mark.parametrize("descriptor_attr", ({}, {"id": "store", "system": ""}))
def test_credentials_skip_profile_reads_without_a_resolved_system(
    descriptor_attr: dict[str, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unexpected_profile_read(_path: Path) -> dict[str, str]:
        raise AssertionError("an unresolved system must not trigger profile I/O")

    monkeypatch.setattr("datamimic_ce.engine.io.connection_config.properties.parse_properties", unexpected_profile_read)

    assert fulfill_credentials(
        descriptor_dir=tmp_path,
        descriptor_attr=descriptor_attr,
        env_props=None,
        system_type="db",
        runtime_environment="production",
        profile_loader=unexpected_profile_read,
    ) == descriptor_attr


def test_descriptor_without_clients_does_not_read_a_credential_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    descriptor = tmp_path / "descriptor.xml"
    descriptor.write_text('<setup><memstore id="rows"/></setup>', encoding="utf-8")

    def unexpected_profile_read(_path: Path) -> dict[str, str]:
        raise AssertionError("a descriptor without clients must not read a credential profile")

    monkeypatch.setattr("datamimic_ce.engine.io.connection_config.properties.parse_properties", unexpected_profile_read)

    setup = DescriptorParser.parse(descriptor, None, "production", profile_loader=load_connection_profile)

    assert len(setup.sub_statements) == 1


def test_nested_static_parser_calls_keep_the_current_production_default(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: list[str] = []

    def parse_sub_elements(
        *_args: object, runtime_environment: str = "production", **_kwargs: object
    ) -> list[Statement]:
        observed.append(runtime_environment)
        return []

    monkeypatch.setattr(dispatch, "parse_sub_elements", parse_sub_elements)

    GenerateParser(ET.fromstring('<generate name="rows" count="1"/>'), {}).parse(
        Path("."), Statement(None, None), profile_loader=load_connection_profile
    )

    assert observed == ["production"]


def test_nested_xml_includes_keep_the_setup_runtime_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_dir = tmp_path / "conf"
    config_dir.mkdir()
    (config_dir / "local.env.properties").write_text(
        "mongo.mongo.host=localhost\nmongo.mongo.port=47017\nmongo.mongo.database=datamimic\n",
        encoding="utf-8",
    )
    (tmp_path / "first.xml").write_text('<setup><include uri="second.xml"/></setup>', encoding="utf-8")
    (tmp_path / "second.xml").write_text('<setup><mongodb id="mongo"/></setup>', encoding="utf-8")
    observed: list[MongoDBStatement] = []

    class CaptureTask(SetupSubTask):
        def __init__(self, statement: MongoDBStatement) -> None:
            self._statement = statement

        @property
        def statement(self) -> MongoDBStatement:
            return self._statement

        def execute(self, _context: SetupContext) -> None:
            observed.append(self._statement)

    def task_for_statement(statement: object, _context: SetupContext) -> IncludeTask | CaptureTask:
        if isinstance(statement, IncludeStatement):
            return IncludeTask(statement)
        assert isinstance(statement, MongoDBStatement)
        return CaptureTask(statement)

    monkeypatch.setattr("datamimic_ce.engine.runtime.tasks.setup.setup_task.create_task", task_for_statement)
    context = SetupContext(
        memstore_manager=None,
        task_id="include-runtime-environment",
        test_mode=True,
        test_result_exporter=None,
        default_separator=",",
        default_locale="en_US",
        default_dataset="US",
        use_mp=False,
        descriptor_dir=tmp_path,
        num_process=None,
        default_variable_prefix="",
        default_variable_suffix="",
        default_line_separator=None,
        runtime_environment="development",
    )

    IncludeTask(IncludeStatement(IncludeModel(uri="first.xml"))).execute(context)

    assert [statement.model.host for statement in observed] == ["localhost"]
