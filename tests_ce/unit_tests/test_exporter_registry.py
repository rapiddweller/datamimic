from datamimic_ce.engine.dsl.vocabulary.constants.exporter_constants import (
    EXPORTER_CSV,
    EXPORTER_DBUNIT,
    EXPORTER_FIXED_WIDTH,
    EXPORTER_JSON,
    EXPORTER_TXT,
    EXPORTER_XLSX,
    EXPORTER_XML,
)
from datamimic_ce.engine.io.api import buffered_exporter_names


def test_registry_publishes_every_buffered_target_name():
    assert buffered_exporter_names() == {
        EXPORTER_CSV,
        EXPORTER_JSON,
        EXPORTER_XML,
        EXPORTER_XLSX,
        EXPORTER_TXT,
        EXPORTER_DBUNIT,
        EXPORTER_FIXED_WIDTH,
    }
