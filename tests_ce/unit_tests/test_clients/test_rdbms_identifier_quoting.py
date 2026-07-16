"""SQL identifier quoting for sequence-backed generators."""

import pytest
from sqlalchemy.dialects import mysql, postgresql

from datamimic_ce.clients.rdbms_client import RdbmsClient


@pytest.mark.parametrize(
    ("dialect", "parts", "expected"),
    [
        (postgresql.dialect(), ("sales-data", "order"), '"sales-data"."order"'),
        (mysql.dialect(), ("sales-data", "order"), "`sales-data`.`order`"),
        (postgresql.dialect(), ('schema"name', 'seq"name'), '"schema""name"."seq""name"'),
    ],
)
def test_qualified_identifier_uses_active_dialect(dialect, parts: tuple[str, ...], expected: str) -> None:
    assert RdbmsClient._quoted_qualified_identifier(dialect, *parts) == expected


def test_qualified_identifier_rejects_empty_parts() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        RdbmsClient._quoted_qualified_identifier(postgresql.dialect(), "public", "")
