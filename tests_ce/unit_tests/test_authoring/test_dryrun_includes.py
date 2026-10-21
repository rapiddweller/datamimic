"""Literal setup includes inherit the same bounded native execution contract."""

import sqlite3
from pathlib import Path, PurePosixPath

import pytest

from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.capture import CaptureStatus
from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest


def _run(root: Path, xml: str, *, smoke_export: bool = False):
    workspace = AuthoringWorkspaceContext(root, PurePosixPath("descriptors/main.xml"))
    return CeBoundedExecutor(workspace).execute(
        BoundedExecutionRequest(
            xml=xml, descriptor_path=workspace.descriptor_path, max_count=3, smoke_export=smoke_export
        )
    )


@pytest.mark.parametrize("included", [False, True])
def test_direct_and_included_products_have_identical_caps(tmp_path: Path, included: bool) -> None:
    directory = tmp_path / "descriptors"
    directory.mkdir()
    generate = (
        '<generate name="rows" count="10" target="JSON"><key name="id" generator="IncrementGenerator"/></generate>'
    )
    (directory / "child.xml").write_text(f"<setup>{generate}</setup>", encoding="utf-8")
    body = '<include uri="child.xml"/>' if included else generate
    before = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}

    result = _run(tmp_path, f'<setup rngSeed="7">{body}</setup>', smoke_export=True)

    assert result.ok, result.diagnostics
    (product,) = result.captured.products
    assert product.rows == ({"id": 1}, {"id": 2}, {"id": 3})
    assert product.capture.status is CaptureStatus.CAPPED
    assert product.capture.requested == 10
    assert product.capture.observed == product.capture.limit == 3
    assert not product.capture.complete
    assert result.smoke_export.applicable_exporters == result.smoke_export.attempted_exporters == 1
    assert result.smoke_export.failed_exporters == 0
    assert {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()} == before


def test_nested_includes_keep_properties_order_scope_and_replay(tmp_path: Path) -> None:
    directory = tmp_path / "descriptors"
    directory.mkdir()
    (directory / "before.properties").write_text("limit=10\nlabel=before\n", encoding="utf-8")
    (directory / "after.properties").write_text("label=after\n", encoding="utf-8")
    (directory / "child.xml").write_text(
        '<setup defaultSeparator=";"><include uri="grandchild.xml"/></setup>', encoding="utf-8"
    )
    (directory / "grandchild.xml").write_text(
        '<setup><generate name="rows" count="{limit}" target="CSV">'
        '<key name="label" constant="{label}"/><key name="context" script="shared"/>'
        "</generate></setup>",
        encoding="utf-8",
    )
    xml = (
        '<setup rngSeed="7"><variable name="shared" constant="visible"/><include uri="before.properties"/>'
        '<include uri="child.xml"/><include uri="after.properties"/>'
        '<generate name="after" count="1"><key name="label" constant="{label}"/></generate></setup>'
    )

    first = _run(tmp_path, xml, smoke_export=True)
    second = _run(tmp_path, xml, smoke_export=True)

    assert first.ok, first.diagnostics
    assert second.ok, second.diagnostics
    assert first.captured == second.captured
    by_name = {product.name: product for product in first.captured.products}
    assert by_name["rows"].rows == ({"label": "before", "context": "visible"},) * 3
    assert by_name["rows"].capture.requested == 10
    assert by_name["after"].rows == ({"label": "after"},)
    assert first.smoke_export.attempted_exporters == 1


@pytest.mark.parametrize("include_depth", [0, 1, 2])
@pytest.mark.parametrize("profile_exists", [False, True])
def test_included_sqlite_uses_workspace_profile_loader(
    tmp_path: Path, include_depth: int, profile_exists: bool
) -> None:
    (tmp_path / "db").mkdir()
    with sqlite3.connect(tmp_path / "db" / "database.sqlite") as connection:
        connection.execute("CREATE TABLE items (id INTEGER)")
        connection.executemany("INSERT INTO items VALUES (?)", [(index,) for index in range(1, 11)])
    body = (
        '<database id="db" dbms="sqlite" database="database" environment="included"/>'
        '<generate name="rows" source="db" selector="SELECT id FROM items" distribution="ordered"/>'
    )
    if profile_exists:
        (tmp_path / "conf").mkdir()
        (tmp_path / "conf" / "included.env.properties").write_text("db.db.database=database\n", encoding="utf-8")
    for depth in range(include_depth):
        name = f"child{depth}.xml"
        (tmp_path / name).write_text(f"<setup>{body}</setup>", encoding="utf-8")
        body = f'<include uri="{name}"/>'
    xml = f"<setup>{body}</setup>"
    before = {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}

    result = CeBoundedExecutor(AuthoringWorkspaceContext(tmp_path)).execute(
        BoundedExecutionRequest(xml=xml, max_count=3)
    )

    assert result.ok, result.diagnostics
    (product,) = result.captured.products
    assert product.rows == ({"id": 1}, {"id": 2}, {"id": 3})
    assert not product.capture.complete
    assert {path.relative_to(tmp_path): path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()} == before


@pytest.mark.parametrize(
    "body",
    [
        '<include uri="missing.xml"/>',
        '<include uri="main.xml"/>',
        '<include uri="child.xml"/>',
        '<include uri="../../outside.xml"/>',
        '<include uri="{dynamic_path}"/>',
        '<generate name="outer" count="1"><include uri="safe.xml"/></generate>',
        '<execute type="bash">echo unsafe</execute>',
        '<execute type="python">import subprocess</execute>',
        '<while condition="True"><echo message="unbounded"/></while>',
        '<execute uri="unsafe.sql"/>',
        "<unsupportedTask/>",
        '<include uri="payload.zip"/>',
    ],
)
def test_unsafe_include_graph_is_rejected_before_any_root_task(tmp_path: Path, body: str) -> None:
    directory = tmp_path / "descriptors"
    directory.mkdir()
    (directory / "safe.xml").write_text('<setup><generate name="rows" count="10"/></setup>', encoding="utf-8")
    (directory / "child.xml").write_text(f"<setup>{body}</setup>", encoding="utf-8")
    (tmp_path / "outside.xml").write_text('<setup><generate name="outside" count="1"/></setup>', encoding="utf-8")
    marker = tmp_path / "executed.txt"
    xml = (
        '<setup><generate name="first" count="1"><key name="x" script="'
        + f"__import__('pathlib').Path({str(marker)!r}).write_text('executed')"
        + '"/></generate><include uri="child.xml"/></setup>'
    )

    result = _run(tmp_path, xml)

    assert not result.ok
    assert not result.captured.products
    assert not marker.exists(), "dependency validation must precede even the first root task"


def test_repeated_included_product_identity_is_refused(tmp_path: Path) -> None:
    directory = tmp_path / "descriptors"
    directory.mkdir()
    (directory / "child.xml").write_text('<setup><generate name="rows" count="2"/></setup>', encoding="utf-8")

    result = _run(tmp_path, '<setup><include uri="child.xml"/><include uri="child.xml"/></setup>')

    assert not result.ok
    assert [diagnostic.code for diagnostic in result.diagnostics] == [AuthoringRuleId.SIDE_EFFECT]


def test_included_smoke_export_inherits_native_separator(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import tempfile

    from datamimic_ce.authoring.adapters.dryrun import _run_engine_capture
    from datamimic_ce.engine.dsl.api import resource_reader_scope

    (tmp_path / "child.xml").write_text('<setup><include uri="grandchild.xml"/></setup>', encoding="utf-8")
    (tmp_path / "grandchild.xml").write_text(
        '<setup><generate name="rows" count="1" target="CSV">'
        '<key name="id" constant="1"/><key name="label" constant="x"/></generate></setup>',
        encoding="utf-8",
    )
    descriptor = tmp_path / "main.xml"
    descriptor.write_text('<setup defaultSeparator=";"><include uri="child.xml"/></setup>', encoding="utf-8")
    artifacts: list[bytes] = []
    cleanup = tempfile.TemporaryDirectory.cleanup

    def collect(directory):
        if Path(directory.name).name.startswith("datamimic_smoke_"):
            artifacts.extend(artifact.read_bytes() for artifact in Path(directory.name).rglob("*.csv"))
        cleanup(directory)

    monkeypatch.setattr(tempfile.TemporaryDirectory, "cleanup", collect)
    with resource_reader_scope(AuthoringWorkspaceContext(tmp_path).read_resource_bytes):
        _run_engine_capture(descriptor, 3, False, True, workspace_root=tmp_path)

    assert artifacts == [b"id;label\r\n1;x\r\n"]


def test_included_memstore_producer_can_supply_root_consumer_without_false_completeness(tmp_path: Path) -> None:
    directory = tmp_path / "descriptors"
    directory.mkdir()
    (directory / "child.xml").write_text(
        '<setup><generate name="rows" count="2" target="store">'
        '<key name="id" generator="IncrementGenerator"/></generate></setup>',
        encoding="utf-8",
    )
    result = _run(
        tmp_path,
        '<setup rngSeed="7"><memstore id="store"/><include uri="child.xml"/>'
        '<generate name="copy" source="store" type="rows" distribution="ordered"/></setup>',
    )

    assert result.ok, result.diagnostics
    by_name = {product.name: product for product in result.captured.products}
    assert by_name["rows"].rows == by_name["copy"].rows == ({"id": 1}, {"id": 2})
    assert by_name["rows"].capture.complete
    assert not by_name["copy"].capture.complete


@pytest.mark.parametrize("root_count", [3, 10])
def test_included_memstore_cannot_claim_a_local_producer_is_the_entire_source(tmp_path: Path, root_count: int) -> None:
    directory = tmp_path / "descriptors"
    directory.mkdir()
    (directory / "child.xml").write_text(
        '<setup><generate name="child_rows" count="3" target="store" targetEntity="rows">'
        '<key name="origin" constant="child"/></generate>'
        '<generate name="copy" source="store" sourceEntity="rows" distribution="ordered"/></setup>',
        encoding="utf-8",
    )
    xml = (
        '<setup rngSeed="7"><memstore id="store"/>'
        + f'<generate name="root_rows" count="{root_count}" target="store" targetEntity="rows">'
        + '<key name="origin" constant="root"/></generate><include uri="child.xml"/></setup>'
    )

    result = _run(tmp_path, xml)

    assert result.ok, result.diagnostics
    products = {product.name: product for product in result.captured.products}
    assert products["copy"].rows == ({"origin": "root"},) * 3
    assert products["copy"].capture.status is CaptureStatus.UNKNOWN
    assert "include" in products["copy"].capture.reason


def test_property_expanded_product_name_cannot_overwrite_capture_provenance(tmp_path: Path) -> None:
    directory = tmp_path / "descriptors"
    directory.mkdir()
    (directory / "names.properties").write_text("alias=rows\n", encoding="utf-8")
    (directory / "child.xml").write_text('<setup><generate name="{alias}" count="3"/></setup>', encoding="utf-8")
    xml = '<setup><include uri="names.properties"/><generate name="rows" count="10"/><include uri="child.xml"/></setup>'

    result = _run(tmp_path, xml)

    assert not result.ok
    assert result.captured.products == ()
    assert [diagnostic.code for diagnostic in result.diagnostics] == [AuthoringRuleId.SIDE_EFFECT]
    assert "capture identities" in result.diagnostics[0].message


def test_linked_include_is_refused_before_content_is_used(tmp_path: Path) -> None:
    directory = tmp_path / "descriptors"
    directory.mkdir()
    (directory / "safe.xml").write_text('<setup><generate name="rows" count="1"/></setup>', encoding="utf-8")
    try:
        (directory / "linked.xml").symlink_to(directory / "safe.xml")
    except OSError:
        pytest.skip("creating symlinks requires host support")

    result = _run(tmp_path, '<setup><include uri="linked.xml"/></setup>')

    assert not result.ok
    assert result.captured.products == ()
