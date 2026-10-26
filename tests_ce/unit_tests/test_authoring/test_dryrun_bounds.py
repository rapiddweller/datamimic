# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Hard bounds, runtime evidence, and process cancellation for authoring dry-runs."""

import time
from pathlib import Path

import pytest

import datamimic_ce.authoring.adapters.dryrun as dryrun_module
from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.capture import CaptureStatus
from datamimic_ce.authoring.domain.diagnostics import AuthoringSystemDiagnosticCode
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest


def _execute_source(xml, **kwargs):
    return CeBoundedExecutor().execute(BoundedExecutionRequest(xml=xml, **kwargs))


def _execute_file(path, **kwargs):
    return CeBoundedExecutor(AuthoringWorkspaceContext(path.parent)).execute(
        BoundedExecutionRequest(xml=path.read_text(encoding="utf-8"), **kwargs)
    )


def test_nested_generate_capture_uses_one_global_limit() -> None:
    xml = """<setup rngSeed="1">
        <generate name="parents" count="1" target="ConsoleExporter">
            <key name="parent_id" generator="IncrementGenerator"/>
            <generate name="children" count="3" target="ConsoleExporter">
                <key name="local_seq" generator="IncrementGenerator"/>
            </generate>
        </generate>
    </setup>"""

    result = _execute_source(xml, max_count=4)

    assert result.ok
    products = {product.name: product for product in result.captured.products}
    child = products["children"]
    assert len(child.rows) == 3
    assert child.capture.status is CaptureStatus.COMPLETE
    assert child.capture.complete
    assert child.capture.requested == 3
    assert child.capture.observed == 3
    assert child.capture.limit == 4


def test_time_series_capture_reports_the_global_limit() -> None:
    xml = (
        '<setup rngSeed="1"><generate name="rows" start="2026-01-01T00:00:00" '
        'end="2026-01-01T03:00:00" interval="PT1H" count="1">'
        '<key name="timestamp" script="ts.now"/></generate></setup>'
    )

    result = _execute_source(xml, max_count=5)

    assert result.ok, result.diagnostics
    product = result.captured.products[0]
    assert len(product.rows) == 3
    assert product.capture.limit == 5


@pytest.mark.parametrize("max_count", [4, 10])
def test_finite_file_source_reports_proven_exhaustion(tmp_path: Path, max_count: int) -> None:
    (tmp_path / "rows.csv").write_text("id|name\n1|A\n2|B\n3|C\n", encoding="utf-8")
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text(
        '<setup rngSeed="1"><generate name="rows" source="rows.csv" '
        'distribution="ordered" target="ConsoleExporter"/></setup>',
        encoding="utf-8",
    )

    result = _execute_file(descriptor, max_count=max_count)

    assert result.ok
    product = result.captured.products[0]
    assert len(product.rows) == 3
    assert product.capture.status is CaptureStatus.EXHAUSTED
    assert product.capture.complete
    assert product.capture.requested == product.capture.observed == 3
    assert product.capture.limit == max_count


def test_finite_file_source_at_limit_is_noncomplete(tmp_path: Path) -> None:
    (tmp_path / "rows.csv").write_text("id\n1\n2\n3\n", encoding="utf-8")
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text(
        '<setup rngSeed="1"><generate name="rows" source="rows.csv" '
        'distribution="ordered" target="ConsoleExporter"/></setup>',
        encoding="utf-8",
    )

    product = _execute_file(descriptor, max_count=1).captured.products[0]

    assert len(product.rows) == 1
    assert product.capture.status is CaptureStatus.CAPPED
    assert not product.capture.complete
    assert product.capture.requested == 3
    assert product.capture.observed == product.capture.limit == 1


def test_file_source_count_failure_remains_unknown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text(
        '<setup rngSeed="1"><generate name="rows" source="rows.csv" '
        'distribution="ordered" target="ConsoleExporter"/></setup>',
        encoding="utf-8",
    )
    from datamimic_ce.engine.dsl.parsers.document.descriptor_parser import DescriptorParser
    from datamimic_ce.engine.io.api import load_connection_profile

    def fail_count(*_args: object) -> int:
        raise OSError("count unavailable")

    monkeypatch.setattr("datamimic_ce.engine.io.api.count_source", fail_count)
    stmt = DescriptorParser.parse(
        descriptor,
        None,
        "production",
        profile_loader=load_connection_profile,
    ).sub_statements[0]

    assert (
        dryrun_module._source_row_count(
            stmt,
            descriptor_dir=tmp_path,
            default_separator="|",
        )
        is None
    )


def test_ranged_counts_are_bounded() -> None:
    # Dynamic counts are evaluated and refused above the limit instead (test_dynamic_count_bounded.py).
    xml = """<setup rngSeed="1">
        <generate name="range" minCount="100" maxCount="200"><key name="x" constant="1"/></generate>
    </setup>"""

    result = _execute_source(xml, max_count=2)

    assert result.ok
    assert {product.name: len(product.rows) for product in result.captured.products} == {"range": 2}
    assert result.captured.products[0].capture.status is CaptureStatus.CAPPED


def test_unique_complete_memstore_producer_proves_finite_readback() -> None:
    xml = """<setup rngSeed="1">
        <memstore id="mem"/>
        <generate name="z_producer" targetEntity="shared" count="8" target="mem">
            <key name="id" generator="IncrementGenerator"/>
        </generate>
        <generate name="a_reader" source="mem" type="shared" distribution="ordered"/>
    </setup>"""

    result = _execute_source(xml, max_count=16)

    products = {product.name: product for product in result.captured.products}
    assert products["z_producer"].capture.status is CaptureStatus.COMPLETE
    reader = products["a_reader"]
    assert len(reader.rows) == 8
    assert reader.capture.status is CaptureStatus.EXHAUSTED
    assert reader.capture.complete
    assert reader.capture.requested == reader.capture.observed == 8
    assert reader.capture.limit == 16


def test_memstore_producer_is_capped_at_global_bound() -> None:
    xml = """<setup rngSeed="1">
        <memstore id="mem"/>
        <generate name="producer" count="8" target="mem">
            <key name="id" generator="IncrementGenerator"/>
        </generate>
    </setup>"""

    result = _execute_source(xml, max_count=4)

    products = {product.name: product for product in result.captured.products}
    assert products["producer"].capture.status is CaptureStatus.CAPPED
    assert len(products["producer"].rows) == 4
    assert products["producer"].capture.limit == 4


def test_memstore_readback_cannot_reuse_the_producers_global_budget() -> None:
    xml = """<setup rngSeed="1">
        <memstore id="mem"/>
        <generate name="producer" count="20" target="mem">
            <key name="id" generator="IncrementGenerator"/>
        </generate>
        <generate name="reader" source="mem" type="producer" distribution="ordered"/>
    </setup>"""

    result = _execute_source(xml, max_count=10)

    assert not result.ok
    assert not result.captured.products


def test_memstore_read_without_generate_producer_is_unknown(tmp_path: Path) -> None:
    (tmp_path / "seed.scr.py").write_text(
        "mem.consume(('shared', [{'id': 1}, {'id': 2}]))\n",
        encoding="utf-8",
    )
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text(
        '<setup rngSeed="1"><memstore id="mem"/><execute uri="seed.scr.py"/>'
        '<generate name="reader" source="mem" type="shared" distribution="ordered"/>'
        "</setup>",
        encoding="utf-8",
    )

    result = _execute_file(
        descriptor,
        allow_side_effects=True,
        max_count=10,
    )

    assert result.ok
    reader = result.captured.products[0]
    assert len(reader.rows) == 2
    assert reader.capture.status is CaptureStatus.UNKNOWN
    assert "no captured producer" in reader.capture.reason


def test_ambiguous_memstore_producers_fail_closed_unknown() -> None:
    xml = """<setup rngSeed="1">
        <memstore id="mem"/>
        <generate name="producer_a" targetEntity="shared" count="2" target="mem">
            <key name="id" generator="IncrementGenerator"/>
        </generate>
        <generate name="producer_b" targetEntity="shared" count="2" target="mem">
            <key name="id" generator="IncrementGenerator"/>
        </generate>
        <generate name="reader" source="mem" type="shared" distribution="ordered"/>
    </setup>"""

    result = _execute_source(xml, max_count=10)

    reader = next(product for product in result.captured.products if product.name == "reader")
    assert len(reader.rows) == 4
    assert reader.capture.status is CaptureStatus.UNKNOWN
    assert "multiple possible producers" in reader.capture.reason


def test_memstore_producer_cycle_fails_closed_unknown(tmp_path: Path) -> None:
    (tmp_path / "seed.scr.py").write_text(
        "store_a.consume(('entity_a', [{'id': 1}]))\nstore_b.consume(('entity_b', [{'id': 2}]))\n",
        encoding="utf-8",
    )
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text(
        '<setup rngSeed="1"><memstore id="store_a"/><memstore id="store_b"/>'
        '<execute uri="seed.scr.py"/>'
        '<generate name="product_a" source="store_b" sourceEntity="entity_b" '
        'target="store_a" targetEntity="entity_a" distribution="ordered"/>'
        '<generate name="product_b" source="store_a" sourceEntity="entity_a" '
        'target="store_b" targetEntity="entity_b" distribution="ordered"/>'
        "</setup>",
        encoding="utf-8",
    )

    products = {
        product.name: product
        for product in _execute_file(
            descriptor,
            allow_side_effects=True,
            max_count=10,
        ).captured.products
    }

    assert products["product_a"].capture.status is CaptureStatus.UNKNOWN
    assert products["product_b"].capture.status is CaptureStatus.UNKNOWN
    assert any(
        "cycle" in product.capture.reason or "not proven complete" in product.capture.reason
        for product in products.values()
    )


def test_timeout_terminates_and_reaps_engine_run(tmp_path: Path) -> None:
    component = tmp_path / "slow.scr.py"
    component.write_text(
        "import time\n"
        "from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator\n"
        "class SlowGenerator(BaseLiteralGenerator):\n"
        "    def generate(self):\n"
        "        time.sleep(2)\n"
        "        return 1\n",
        encoding="utf-8",
    )
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text(
        '<setup><execute uri="slow.scr.py"/><generate name="one" count="1">'
        '<key name="x" generator="SlowGenerator()"/></generate></setup>',
        encoding="utf-8",
    )
    started = time.perf_counter()

    result = _execute_file(
        descriptor,
        allow_side_effects=True,
        timeout_seconds=1,
    )

    elapsed = time.perf_counter() - started
    assert elapsed <= 5
    assert not result.ok
    assert result.diagnostics[0].code is AuthoringSystemDiagnosticCode.TIMEOUT


def test_successful_dry_run_executes_engine_once(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "engine-runs.txt"
    component = tmp_path / "counting.scr.py"
    component.write_text(
        "from pathlib import Path\n"
        "from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator\n"
        f"MARKER = Path({str(marker)!r})\n"
        "class CountingGenerator(BaseLiteralGenerator):\n"
        "    def generate(self):\n"
        "        previous = MARKER.read_text() if MARKER.exists() else ''\n"
        "        MARKER.write_text(previous + 'run\\n')\n"
        "        return 1\n",
        encoding="utf-8",
    )
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text(
        '<setup rngSeed="1"><execute uri="counting.scr.py"/>'
        '<generate name="one" count="1"><key name="x" '
        'generator="CountingGenerator()"/></generate></setup>',
        encoding="utf-8",
    )

    result = _execute_file(descriptor, allow_side_effects=True)

    assert result.ok
    assert marker.read_text(encoding="utf-8").splitlines() == ["run"]
