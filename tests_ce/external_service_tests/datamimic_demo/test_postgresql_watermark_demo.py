from datetime import datetime
from pathlib import Path

import pytest

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

ROOT = Path(__file__).resolve().parents[3]


def rows(connection, query: str) -> list[tuple]:
    with connection.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()


@pytest.mark.parametrize(
    "postgres_demo",
    [
        ("datamimic_ce/resources/demos/demo-watermark", ("source", "config", "target")),
        ("tests_ce/external_service_tests/datamimic_demo/k-watermark", ("source", "config", "target")),
    ],
    indirect=True,
)
def test_postgresql_watermark_demo_root(postgres_demo) -> None:
    demo, connections = postgres_demo
    before = datetime.now()
    DataMimicTest(demo, "datamimic.xml").test_with_timer()
    after = datetime.now()
    source = rows(connections["source"], "SELECT id, no, name, company, date FROM data ORDER BY id")
    target = rows(connections["target"], "SELECT id, no, name, company, date FROM data ORDER BY id")
    watermark = rows(connections["config"], "SELECT key_column, value_column FROM watermark")
    assert len(source) == len(target) == 10
    assert [row[0] for row in source] == list(range(1, 11))
    assert [(row[0], row[1], row[4]) for row in target] == [(row[0], row[1], row[4]) for row in source]
    assert all(isinstance(row[4], datetime) for row in source + target)
    assert all(row[2] and row[3] for row in target)
    assert any(original[2:4] != masked[2:4] for original, masked in zip(source, target, strict=True))
    assert len(watermark) == 1
    assert watermark[0][0] == "last_processed_datetime"
    final_timestamp = watermark[0][1]
    assert isinstance(final_timestamp, datetime)
    assert before <= final_timestamp <= after
    assert max(row[4] for row in source) <= final_timestamp
