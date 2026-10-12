"""A descriptor script can call the one-argument raw Memstore getter."""

from pathlib import Path

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


def test_raw_getter_is_visible_to_descriptor_scripts(tmp_path: Path) -> None:
    descriptor = tmp_path / "raw_memstore_read.xml"
    descriptor.write_text(
        """<setup>
    <memstore id="mem"/>
    <generate name="rows" count="1" target="mem">
        <key name="value" constant="42"/>
    </generate>
    <generate name="result" count="1" target="JSON">
        <key name="value" script="mem.get_data_by_type('rows')[0]['value']"/>
    </generate>
</setup>
""",
        encoding="utf-8",
    )

    engine = DataMimicTest(tmp_path, descriptor.name, capture_test_result=True)
    engine.test_with_timer()

    assert engine.capture_result()["result"] == [{"value": "42"}]
