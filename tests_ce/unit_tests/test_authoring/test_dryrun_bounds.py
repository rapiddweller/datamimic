# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Hard bounds, runtime evidence, and process cancellation for authoring dry-runs."""

import multiprocessing as mp
import time
from pathlib import Path

import pytest

import datamimic_ce.authoring.dryrun as dryrun_module
from datamimic_ce.authoring.contracts import CaptureStatus
from datamimic_ce.authoring.dryrun import dry_run_captured, dry_run_source


def test_nested_generate_count_is_bounded_per_parent() -> None:
    xml = """<setup rngSeed="1">
        <generate name="parents" count="1" target="ConsoleExporter">
            <key name="parent_id" generator="IncrementGenerator"/>
            <generate name="children" count="3" target="ConsoleExporter">
                <key name="local_seq" generator="IncrementGenerator"/>
            </generate>
        </generate>
    </setup>"""

    result = dry_run_source(xml, max_count=1, sample_rows=5)

    assert result.ok
    products = {product.name: product for product in result.products}
    child = products["children"]
    assert child.count == 1
    assert child.capture.status is CaptureStatus.CAPPED
    assert not child.capture.complete
    assert child.capture.requested == 3
    assert child.capture.observed == child.capture.limit == 1


@pytest.mark.parametrize("max_count", [4, 10])
def test_finite_file_source_reports_proven_exhaustion(tmp_path: Path, max_count: int) -> None:
    (tmp_path / "rows.csv").write_text("id|name\n1|A\n2|B\n3|C\n", encoding="utf-8")
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text(
        '<setup rngSeed="1"><generate name="rows" source="rows.csv" '
        'distribution="ordered" target="ConsoleExporter"/></setup>',
        encoding="utf-8",
    )

    result = dry_run_captured(descriptor, max_count=max_count).result

    assert result.ok
    product = result.products[0]
    assert product.count == 3
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

    product = dry_run_captured(descriptor, max_count=1).result.products[0]

    assert product.count == 1
    assert product.capture.status is CaptureStatus.CAPPED
    assert not product.capture.complete
    assert product.capture.requested == 3
    assert product.capture.observed == product.capture.limit == 1


def test_dynamic_and_ranged_counts_are_bounded() -> None:
    xml = """<setup rngSeed="1">
        <generate name="dynamic" count="{1000}"><key name="x" constant="1"/></generate>
        <generate name="range" minCount="100" maxCount="200"><key name="x" constant="1"/></generate>
        <generate name="minimum" minCount="100"><key name="x" constant="1"/></generate>
    </setup>"""

    result = dry_run_source(xml, max_count=2)

    assert result.ok
    assert {product.name: product.count for product in result.products} == {
        "dynamic": 2,
        "minimum": 2,
        "range": 2,
    }
    assert all(product.capture.status is CaptureStatus.CAPPED for product in result.products)


def test_unique_complete_memstore_producer_proves_finite_readback() -> None:
    xml = """<setup rngSeed="1">
        <memstore id="mem"/>
        <generate name="z_producer" type="shared" count="8" target="mem">
            <key name="id" generator="IncrementGenerator"/>
        </generate>
        <generate name="a_reader" source="mem" type="shared" distribution="ordered"/>
    </setup>"""

    result = dry_run_source(xml, max_count=10)

    products = {product.name: product for product in result.products}
    assert products["z_producer"].capture.status is CaptureStatus.COMPLETE
    reader = products["a_reader"]
    assert reader.count == 8
    assert reader.capture.status is CaptureStatus.EXHAUSTED
    assert reader.capture.complete
    assert reader.capture.requested == reader.capture.observed == 8
    assert reader.capture.limit == 10


def test_memstore_reader_is_noncomplete_when_global_bound_caps_producer() -> None:
    xml = """<setup rngSeed="1">
        <memstore id="mem"/>
        <generate name="producer" count="8" target="mem">
            <key name="id" generator="IncrementGenerator"/>
        </generate>
        <generate name="reader" source="mem" type="producer" distribution="ordered"/>
    </setup>"""

    result = dry_run_source(xml, max_count=4)

    products = {product.name: product for product in result.products}
    assert products["producer"].capture.status is CaptureStatus.CAPPED
    assert not products["reader"].capture.complete
    assert products["reader"].capture.status is CaptureStatus.UNKNOWN


def test_capped_memstore_producer_propagates_unknown_to_full_bounded_reader() -> None:
    xml = """<setup rngSeed="1">
        <memstore id="mem"/>
        <generate name="producer" count="20" target="mem">
            <key name="id" generator="IncrementGenerator"/>
        </generate>
        <generate name="reader" source="mem" type="producer" distribution="ordered"/>
    </setup>"""

    products = {
        product.name: product for product in dry_run_source(xml, max_count=10).products
    }

    assert products["producer"].capture.status is CaptureStatus.CAPPED
    assert products["reader"].count == 10
    assert products["reader"].capture.status is CaptureStatus.UNKNOWN
    assert "producer capture" in products["reader"].capture.reason


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

    result = dry_run_captured(
        descriptor,
        allow_side_effects=True,
        max_count=10,
    ).result

    assert result.ok
    reader = result.products[0]
    assert reader.count == 2
    assert reader.capture.status is CaptureStatus.UNKNOWN
    assert "no captured producer" in reader.capture.reason


def test_ambiguous_memstore_producers_fail_closed_unknown() -> None:
    xml = """<setup rngSeed="1">
        <memstore id="mem"/>
        <generate name="producer_a" type="shared" count="2" target="mem">
            <key name="id" generator="IncrementGenerator"/>
        </generate>
        <generate name="producer_b" type="shared" count="2" target="mem">
            <key name="id" generator="IncrementGenerator"/>
        </generate>
        <generate name="reader" source="mem" type="shared" distribution="ordered"/>
    </setup>"""

    result = dry_run_source(xml, max_count=10)

    reader = next(product for product in result.products if product.name == "reader")
    assert reader.count == 4
    assert reader.capture.status is CaptureStatus.UNKNOWN
    assert "multiple possible producers" in reader.capture.reason


def test_memstore_producer_cycle_fails_closed_unknown(tmp_path: Path) -> None:
    (tmp_path / "seed.scr.py").write_text(
        "store_a.consume(('entity_a', [{'id': 1}]))\n"
        "store_b.consume(('entity_b', [{'id': 2}]))\n",
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
        for product in dry_run_captured(
            descriptor,
            allow_side_effects=True,
            max_count=10,
        ).result.products
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
    before = {process.pid for process in mp.active_children()}
    started = time.perf_counter()

    result = dry_run_captured(
        descriptor,
        allow_side_effects=True,
        timeout_seconds=1,
    ).result

    elapsed = time.perf_counter() - started
    assert elapsed <= 1.5
    assert not result.ok
    assert [diagnostic.rule for diagnostic in result.diagnostics] == ["DM002"]
    assert "terminated" in result.diagnostics[0].message
    assert {process.pid for process in mp.active_children()} == before


def test_process_context_is_explicit_and_worker_is_spawn_safe() -> None:
    assert dryrun_module._process_context().get_start_method() == "spawn"
    assert dryrun_module._engine_process_worker.__module__ == dryrun_module.__name__


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

    result = dry_run_captured(descriptor, allow_side_effects=True).result

    assert result.ok
    assert marker.read_text(encoding="utf-8").splitlines() == ["run"]
