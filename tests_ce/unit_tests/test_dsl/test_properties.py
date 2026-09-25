from pathlib import Path
from typing import Literal

import pytest

from datamimic_ce.engine.dsl.api import parse_properties
from datamimic_ce.engine.dsl.parsers.descriptor_parser import DescriptorParser
from datamimic_ce.engine.dsl.parsers.parser_util import ParserUtil
from datamimic_ce.engine.dsl.statements.mongodb_statement import MongoDBStatement
from datamimic_ce.engine.io.api import FileUtil


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

    credentials = ParserUtil.fulfill_credentials(
        descriptor_dir=tmp_path,
        descriptor_attr={"id": "store"},
        env_props=None,
        system_type="db",
        runtime_environment=runtime_environment,
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

    setup = DescriptorParser.parse(descriptor, None, "development")

    mongodb = setup.sub_statements[0]
    assert isinstance(mongodb, MongoDBStatement)
    assert mongodb.model.host == "localhost"
