from datamimic_ce.constants.exporter_constants import (
    EXPORTER_CSV,
    EXPORTER_DBUNIT,
    EXPORTER_JSON,
    EXPORTER_TXT,
    EXPORTER_XLSX,
    EXPORTER_XML,
)
from datamimic_ce.exporters.csv_exporter import CSVExporter
from datamimic_ce.exporters.dbunit_exporter import DbUnitExporter
from datamimic_ce.exporters.exporter_util import _BUFFERED_EXPORTERS
from datamimic_ce.exporters.json_exporter import JsonExporter
from datamimic_ce.exporters.txt_exporter import TXTExporter
from datamimic_ce.exporters.unified_buffered_exporter import UnifiedBufferedExporter
from datamimic_ce.exporters.xlsx_exporter import XLSXExporter
from datamimic_ce.exporters.xml_exporter import XMLExporter


def test_registry_maps_every_buffered_target_to_its_class():
    assert {
        EXPORTER_CSV: CSVExporter,
        EXPORTER_JSON: JsonExporter,
        EXPORTER_XML: XMLExporter,
        EXPORTER_XLSX: XLSXExporter,
        EXPORTER_TXT: TXTExporter,
        EXPORTER_DBUNIT: DbUnitExporter,
    } == _BUFFERED_EXPORTERS


def test_every_registered_exporter_is_a_buffered_exporter_with_a_uniform_ctor():
    import inspect

    for cls in _BUFFERED_EXPORTERS.values():
        assert issubclass(cls, UnifiedBufferedExporter)
        # uniform constructor: (self, config, params)
        assert list(inspect.signature(cls.__init__).parameters)[1:] == ["config", "params"]
