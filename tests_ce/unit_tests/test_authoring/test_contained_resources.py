"""Property expansion and caches cannot bypass contained descriptor resource reads."""

import os
from pathlib import Path

import pytest

from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
from datamimic_ce.authoring.adapters.validator import CeDescriptorValidator
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest


def test_host_validator_never_reads_escaping_properties(tmp_path, monkeypatch):
    root = tmp_path / "workspace"
    root.mkdir()
    outside = tmp_path / "outside.properties"
    outside.write_text("count=1\n")
    workspace = AuthoringWorkspaceContext(root)
    opened = []
    original = Path.open

    def observe(path, *args, **kwargs):
        if path.resolve() == outside:
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    result = CeDescriptorValidator(workspace, profile_loader=workspace.load_connection_profile).validate(
        '<setup><include uri="../outside.properties"/><generate name="rows" count="{count}"><key name="x" constant="1"/></generate></setup>'
    )
    assert not opened, "rejection must happen before host property content is opened"
    assert not result.ok


def test_cached_properties_cannot_bypass_host_validator_containment(tmp_path):
    from datamimic_ce.engine.dsl.api import parse_properties

    root = tmp_path / "workspace"
    root.mkdir()
    outside = tmp_path / "outside.properties"
    outside.write_text("count=1\n")
    assert parse_properties(outside) == {"count": "1"}
    workspace = AuthoringWorkspaceContext(root)
    result = CeDescriptorValidator(workspace, profile_loader=workspace.load_connection_profile).validate(
        '<setup><include uri="../outside.properties"/><generate name="rows" count="1"><key name="x" constant="1"/></generate></setup>'
    )
    assert not result.ok


def test_property_expanded_file_source_cannot_read_outside_snapshot(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    outside = tmp_path / "outside.csv"
    outside.write_text("secret\nprivate-outside-value\n")
    (root / "input.properties").write_text(f"location={outside.as_posix()}\n")
    xml = '<setup><include uri="input.properties"/><generate name="rows" source="{location}" distribution="ordered"/></setup>'
    result = CeBoundedExecutor(AuthoringWorkspaceContext(root)).execute(BoundedExecutionRequest(xml=xml))
    assert not result.ok, result.captured
    assert not result.captured.products
    assert all("private-outside-value" not in diagnostic.message for diagnostic in result.diagnostics)


@pytest.mark.skipif(os.name != "posix", reason="POSIX nofollow race; Windows actual handle controls are separate")
def test_profile_symlink_swap_is_rejected_before_read(tmp_path, monkeypatch):
    root = tmp_path / "workspace"
    (root / "conf").mkdir(parents=True)
    profile = root / "conf" / "environment.env.properties"
    profile.write_text("db.db.database=inside\n")
    outside = tmp_path / "outside.properties"
    outside.write_text("db.db.database=private-outside\n")
    workspace = AuthoringWorkspaceContext(root)
    original_path_open = Path.open
    original_os_open = os.open
    swapped = False

    def swap():
        nonlocal swapped
        if not swapped:
            swapped = True
            profile.unlink()
            profile.symlink_to(outside)

    def race_path(path, *args, **kwargs):
        if path.name == profile.name:
            swap()
        return original_path_open(path, *args, **kwargs)

    def race_descriptor(path, flags, *args, **kwargs):
        if Path(path).name == profile.name:
            swap()
        return original_os_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(Path, "open", race_path)
    monkeypatch.setattr(os, "open", race_descriptor)
    with pytest.raises((OSError, ValueError)):
        workspace.load_connection_profile(root, "environment")
    assert swapped


def test_contained_expanded_source_preserves_relative_identity(tmp_path):
    root = tmp_path / "workspace"
    (root / "descriptors").mkdir(parents=True)
    (root / "data").mkdir()
    (root / "data" / "rows.csv").write_text("id|name\n1|inside\n2|second\n")
    (root / "descriptors" / "input.properties").write_text("location=../data/rows.csv\n")
    from pathlib import PurePosixPath

    logical = PurePosixPath("descriptors/model.xml")
    xml = '<setup><include uri="input.properties"/><generate name="rows" source="{location}" distribution="ordered"/></setup>'
    workspace = AuthoringWorkspaceContext(root, logical)
    result = CeBoundedExecutor(workspace).execute(BoundedExecutionRequest(xml=xml, descriptor_path=logical))
    assert result.ok, result.diagnostics
    assert result.captured.products[0].rows == ({"id": "1", "name": "inside"}, {"id": "2", "name": "second"})


@pytest.mark.parametrize("format_name", ["csv", "json", "xml", "dbunit", "fixed", "xlsx"])
def test_all_file_readers_reject_outside_before_content_read(tmp_path, monkeypatch, format_name):
    from datamimic_ce.engine.dsl.api import parse_xml_file, resource_reader_scope
    from datamimic_ce.engine.io.files.readers import FileUtil

    root = tmp_path / "workspace"
    root.mkdir()
    outside = tmp_path / "outside.dat"
    outside.write_bytes(b"private-outside")
    workspace = AuthoringWorkspaceContext(root)
    readers = {
        "csv": lambda: FileUtil.read_csv_to_dict_list(outside, "|"),
        "json": lambda: FileUtil.read_json(outside),
        "xml": lambda: parse_xml_file(outside),
        "dbunit": lambda: FileUtil.read_dbunit_to_dict_list(outside, "rows"),
        "fixed": lambda: FileUtil.read_fixed_width_to_dict_list(outside),
        "xlsx": lambda: FileUtil.read_xlsx_to_dict_list(outside),
    }
    original = Path.open
    opened = []

    def observe(path, *args, **kwargs):
        if path == outside:
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    with resource_reader_scope(workspace.read_resource_bytes), pytest.raises(ValueError):
        readers[format_name]()
    assert not opened


def test_scoped_file_cache_is_bypassed_and_reader_scope_restores(tmp_path):
    from datamimic_ce.engine.dsl.api import resource_reader_scope
    from datamimic_ce.engine.io.files.readers import FileUtil

    root = tmp_path / "workspace"
    root.mkdir()
    outside = tmp_path / "outside.csv"
    outside.write_text("id\nprivate-outside\n")
    assert FileUtil.read_csv_to_dict_list(outside, "|") == [{"id": "private-outside"}]
    with resource_reader_scope(AuthoringWorkspaceContext(root).read_resource_bytes), pytest.raises(ValueError):
        FileUtil.read_csv_to_dict_list(outside, "|")
    assert FileUtil.read_csv_to_dict_list(outside, "|") == [{"id": "private-outside"}]


def test_host_validator_accepts_contained_property_include(tmp_path):
    (tmp_path / "input.properties").write_text("rows=2\n")
    workspace = AuthoringWorkspaceContext(tmp_path)
    result = CeDescriptorValidator(workspace, profile_loader=workspace.load_connection_profile).validate(
        '<setup rngSeed="1"><include uri="input.properties"/><generate name="rows" count="{rows}"><key name="id" constant="1"/></generate></setup>'
    )
    assert result.ok, result.diagnostics


def test_scoped_properties_ignore_stale_normal_cache(tmp_path):
    from datamimic_ce.engine.dsl.api import parse_properties, resource_reader_scope

    path = tmp_path / "input.properties"
    path.write_text("rows=1\n")
    assert parse_properties(path) == {"rows": "1"}
    path.write_text("rows=2\n")
    with resource_reader_scope(AuthoringWorkspaceContext(tmp_path).read_resource_bytes):
        assert parse_properties(path) == {"rows": "2"}
    assert parse_properties(path) == {"rows": "1"}


def test_bounded_builtin_sector_generator_keeps_packaged_dataset_access():
    xml = '<setup rngSeed="1"><generate name="rows" count="1"><key name="country" generator="SectorGenerator"/></generate></setup>'
    result = CeBoundedExecutor().execute(BoundedExecutionRequest(xml=xml))
    assert result.ok, result.diagnostics
    assert len(result.captured.products[0].rows) == 1


def test_country_domain_dataset_remains_available_inside_resource_scope(tmp_path):
    from datamimic_ce.domains.shared.generators.country_generator import CountryGenerator
    from datamimic_ce.engine.dsl.api import resource_reader_scope

    with resource_reader_scope(AuthoringWorkspaceContext(tmp_path).read_resource_bytes):
        assert CountryGenerator(dataset="US").get_country_by_iso_code("US")[0] == "US"


def test_custom_dataset_paths_do_not_inherit_packaged_trust(tmp_path):
    from datamimic_ce.domains.shared.datasets.loader import read_csv_rows
    from datamimic_ce.engine.dsl.api import resource_reader_scope

    root = tmp_path / "workspace"
    root.mkdir()
    outside = tmp_path / "custom.csv"
    outside.write_text("private-outside\n")
    with resource_reader_scope(AuthoringWorkspaceContext(root).read_resource_bytes), pytest.raises(ValueError):
        read_csv_rows(outside)


@pytest.mark.parametrize("override", ["DATAMIMIC_DOMAIN_DATA", "DATAMIMIC_ROOT"])
def test_bounded_run_rejects_inherited_dataset_root_before_any_read(tmp_path, monkeypatch, override):
    from datamimic_ce.authoring.domain.diagnostics import AuthoringSystemDiagnosticCode

    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "private.csv"
    sentinel.write_text("private-outside\n")
    opened = []
    original = Path.open

    def observe(path, *args, **kwargs):
        if path.is_relative_to(outside):
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    monkeypatch.setenv(override, str(outside))
    monkeypatch.setattr(
        CeBoundedExecutor, "_execute_child", lambda *args: pytest.fail("configured roots reached child")
    )
    result = CeBoundedExecutor().execute(
        BoundedExecutionRequest(
            xml='<setup rngSeed="1"><generate name="rows" count="1"><key name="sector" generator="SectorGenerator"/></generate></setup>'
        )
    )
    assert not result.ok
    assert result.diagnostics[0].code is AuthoringSystemDiagnosticCode.ENVIRONMENT
    assert not opened
    assert sentinel.read_text() == "private-outside\n"
