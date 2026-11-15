from pathlib import Path

import psycopg2
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
        ("datamimic_ce/resources/demos/demo-db-mapping", ("mapping",)),
        ("tests_ce/external_service_tests/datamimic_demo/demo-db-mapping", ("mapping",)),
    ],
    indirect=True,
)
def test_postgresql_mapping_demo_root(postgres_demo) -> None:
    import csv

    demo, connections = postgres_demo
    engine = DataMimicTest(demo, "datamimic.xml", capture_test_result=True)
    engine.test_with_timer()
    connection = connections["mapping"]
    with (demo / "data/business_mapping.ent.csv").open() as source:
        expected = list(csv.DictReader(source, delimiter="|"))
    actual = rows(
        connection,
        'SELECT "idTop", "idSub", "countryCode", city, "postCode", description, title, title_description FROM business_mapping ORDER BY "idTop"',
    )
    assert actual == [
        (
            int(row["idTop"]),
            int(row["idSub"]),
            row["countryCode"],
            row["city"],
            row["postCode"],
            row["description"],
            row["title"],
            row["title_description"],
        )
        for row in sorted(expected, key=lambda row: int(row["idTop"]))
    ]
    assert len(actual) == 1000
    with pytest.raises(psycopg2.errors.NotNullViolation):
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO business_mapping (city) VALUES ('missing-key')")
    connection.rollback()
    result = engine.capture_result()
    assert result is not None
    transactions = result["transaction_record"]
    assert len(transactions) == 100
    for transaction in transactions:
        assert len(transaction["transaction_details"]) == 10
        for detail in transaction["transaction_details"]:
            assert any(
                (detail["account_id"], detail["branch_id"], transaction["city"]) == (row[0], row[1], row[3])
                for row in actual
            )
