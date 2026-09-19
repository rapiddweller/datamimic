# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Runtime length classification must consume the central source-suffix fact."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from datamimic_ce.data_sources.data_source_registry import DataSourceRegistry
from datamimic_ce.model.constraints import SourceFileFormat, source_capabilities
from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.statements.nested_key_statement import NestedKeyStatement
from datamimic_ce.statements.variable_statement import VariableStatement
from datamimic_ce.utils.file_util import FileUtil


def _context() -> tuple[Mock, Mock]:
    root = Mock()
    root.data_source_len = {}
    root.descriptor_dir = Path("/descriptor")
    root.default_separator = "|"
    root.memstore_manager.contain.return_value = False
    root.get_client_by_id.return_value = None
    context = Mock()
    context.root = root
    return context, root


def _statement(
    statement_type: type[GenerateStatement | VariableStatement | NestedKeyStatement],
    source: str,
    source_type: str,
) -> GenerateStatement | VariableStatement | NestedKeyStatement:
    statement = object.__new__(statement_type)
    statement._full_name = "consumer"
    statement._name = "consumer"
    statement._source = source
    statement._source_entity = "rows"
    statement._type = source_type
    statement._separator = None
    if isinstance(statement, GenerateStatement):
        statement._script = None
        statement._offset = None
    return statement


_LENGTH_SOURCE_CASES = tuple(
    (capability.element, capability.source_type, file_format)
    for capability in source_capabilities()
    if capability.element in {"generate", "iterate", "variable", "nestedKey"}
    for file_format in capability.file_formats
)


@pytest.mark.parametrize(("element", "source_type", "file_format"), _LENGTH_SOURCE_CASES)
def test_length_classification_uses_every_central_file_suffix(
    element: str,
    source_type: str | None,
    file_format: SourceFileFormat,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, root = _context()
    statement_type = (
        VariableStatement
        if element == "variable"
        else NestedKeyStatement
        if element == "nestedKey"
        else GenerateStatement
    )
    statement = _statement(statement_type, f"rows{file_format.value}", source_type or "rows")
    generic = Mock(return_value=[{}, {}])
    dbunit = Mock(return_value=[{}, {}, {}])
    monkeypatch.setattr(DataSourceRegistry, "_get_source", generic)
    monkeypatch.setattr(FileUtil, "read_dbunit_to_dict_list", dbunit)

    DataSourceRegistry.set_data_source_length(context, statement)
    cache_key = ("consumer", f"rows{file_format.value}")

    if file_format is SourceFileFormat.DBUNIT_XML:
        assert root.data_source_len[cache_key] == 3
        dbunit.assert_called_once_with(Path("/descriptor/rows.dbunit.xml"), "rows")
        generic.assert_not_called()
    else:
        assert root.data_source_len[cache_key] == 2
        generic.assert_called_once_with(f"/descriptor/rows{file_format.value}", "|", file_format)
        dbunit.assert_not_called()


def test_nonfile_source_still_uses_memstore_classification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context, root = _context()
    statement = _statement(VariableStatement, "upstream_rows", "rows")
    statement._source_entity = None
    memstore = Mock()
    memstore.get_data_len_by_type.return_value = 5
    root.memstore_manager.contain.return_value = True
    root.memstore_manager.get_memstore.return_value = memstore
    generic = Mock(return_value=[])
    monkeypatch.setattr(DataSourceRegistry, "_get_source", generic)

    DataSourceRegistry.set_data_source_length(context, statement)

    assert root.data_source_len[("consumer", "upstream_rows")] == 5
    root.memstore_manager.get_memstore.assert_called_once_with("upstream_rows")
    memstore.get_data_len_by_type.assert_called_once_with("rows")
    generic.assert_not_called()
