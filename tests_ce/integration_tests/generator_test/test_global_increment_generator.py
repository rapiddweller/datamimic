import os
from pathlib import Path

import pytest

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


class TestGlobalIncrementGenerator:
    _test_dir = Path(__file__).resolve().parent

    def test_global_increment_generator(self):
        """
        Ensure GlobalIncrementGenerator yields globally unique, contiguous IDs
        across nested generate blocks.

        Descriptor: global_increment_generator_test.xml
        - customers: count=10, numProcess=1
        - orders per customer: 3
        - line_items per order: 3
        Expectation:
        - customers.cId: 1..10
        - orders.oId: 1..30
        - line_items.lId: 1..90
        """
        engine = DataMimicTest(
            test_dir=self._test_dir,
            filename="global_increment_generator_test.xml",
            capture_test_result=True,
        )
        engine.test_with_timer()
        cap = engine.capture_result()

        # Outermost
        customers = cap["customers"]
        c_ids = [int(r["cId"]) for r in customers]
        assert c_ids == list(range(1, 11))

        # Nested level 1
        orders = cap["orders"]
        o_ids = [int(r["oId"]) for r in orders]
        assert o_ids == list(range(1, 31))

        # Nested level 2 (note: key becomes 'orders|line_items' after trimming the first segment)
        line_items = cap["orders|line_items"]
        l_ids = [int(r["lId"]) for r in line_items]
        assert l_ids == list(range(1, 91))

        # Additional safety: uniqueness
        assert len(set(c_ids)) == len(c_ids)
        assert len(set(o_ids)) == len(o_ids)
        assert len(set(l_ids)) == len(l_ids)


def _run_descriptor(tmp_path, platform, fields, *, seed=None, workers=2):
    from datamimic_ce.engine.runtime.api import run
    from datamimic_ce.engine.runtime.contracts import RunRequest

    seed_attr = f' rngSeed="{seed}"' if seed is not None else ""
    (tmp_path / "helpers.py").write_text("def worker_pid():\n    import os\n    return os.getpid()\n")
    descriptor = tmp_path / "global_increment.xml"
    descriptor.write_text(
        f'<setup multiprocessing="True" numProcess="{workers}"{seed_attr}>'
        '<execute type="python" uri="helpers.py"/>'
        f'<generate name="rows" count="8" pageSize="2" mpPlatform="{platform}" target="">'
        '<key name="pid" script="worker_pid()"/>'
        f'{fields}</generate></setup>'
    )
    return run(RunRequest(descriptor_path=descriptor, test_mode=True)).captured


def _global_fields(nested):
    if not nested:
        return '<key name="id" generator="GlobalIncrementGenerator"/>'
    # Only descendants use the global counter: the outer scheduler must find it
    # through both condition wrappers and nested generation before copying state.
    return '''<condition><if condition="True">
        <generate name="children" count="3" pageSize="2" target="">
            <variable name="seq" generator="GlobalIncrementGenerator()"/>
            <key name="id" script="seq"/>
            <key name="other" generator="GlobalIncrementGenerator"/>
            <generate name="grandchildren" count="2" pageSize="1" target="">
                <key name="id" generator="GlobalIncrementGenerator"/>
            </generate>
        </generate>
    </if></condition>'''


@pytest.mark.parametrize("platform", ["multiprocessing", "ray"])
@pytest.mark.parametrize("nested", [False, True])
def test_requested_workers_keep_global_ids_unique(tmp_path, platform, nested):
    captured = _run_descriptor(tmp_path, platform, _global_fields(nested))
    assert captured is not None
    product, count = ("children", 24) if nested else ("rows", 8)
    ids = [row["id"] for row in captured[product]]
    assert ids == list(range(1, count + 1)), ids
    # Serial execution is the CE policy for a process-local global counter.
    assert {row["pid"] for row in captured["rows"]} == {os.getpid()}
    if nested:
        assert [row["other"] for row in captured["children"]] == list(range(1, 25))
        assert [row["id"] for row in captured["children|grandchildren"]] == list(range(1, 49))


def test_ordinary_increment_keeps_backend_workers(tmp_path):
    captured = _run_descriptor(tmp_path, "multiprocessing", '<key name="id" generator="IncrementGenerator"/>')
    assert captured is not None
    assert [row["id"] for row in captured["rows"]] == list(range(1, 9))
    assert os.getpid() not in {row["pid"] for row in captured["rows"]}


def test_global_increment_seeded_nested_replay_and_fresh_run(tmp_path):
    fields = _global_fields(True)
    first = _run_descriptor(tmp_path, "multiprocessing", fields, seed=17)
    assert first == _run_descriptor(tmp_path, "ray", fields, seed=17)
    assert first == _run_descriptor(tmp_path, "multiprocessing", fields, seed=17, workers=1)
    assert [row["id"] for row in first["children"]] == list(range(1, 25))


def test_global_increment_xml_attributes_continue_across_pages(tmp_path):
    fields = '<key name="value" constant="text"><element name="id" generator="GlobalIncrementGenerator"/></key>'
    captured = _run_descriptor(tmp_path, "multiprocessing", fields)
    assert [row["value"]["@id"] for row in captured["rows"]] == list(range(1, 9))


def test_repeated_includes_keep_independent_counter_contexts(tmp_path):
    (tmp_path / "included.xml").write_text('''<setup multiprocessing="True" numProcess="2">
        <generate name="rows" count="2" pageSize="1" target="">
            <key name="id" generator="GlobalIncrementGenerator"/>
        </generate>
    </setup>''')
    (tmp_path / "includes.xml").write_text('''<setup>
        <include uri="included.xml"/>
        <include uri="included.xml"/>
    </setup>''')
    engine = DataMimicTest(test_dir=tmp_path, filename="includes.xml", capture_test_result=True)
    engine.test_with_timer()
    # Includes clone their owning root setup context; they do not share a
    # descriptor-wide counter just because the qualified field names match.
    assert [row["id"] for row in engine.capture_result()["rows"]] == [1, 2, 1, 2]
