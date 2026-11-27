# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Binding a whole entity (<key script="person">) into a scalar RDBMS column - migration parity
(the legacy toString()). Confirmed empirically before this fix: sqlite3.ProgrammingError,
'type Person is not supported' - so this is a pure improvement, not a behavior change with
regression risk (nothing succeeds today for this input)."""

import sqlite3
from contextlib import closing

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


def test_entity_stringify_rdbms(project_dir):
    """capture_result() reflects the generated record BEFORE export-time normalization (the
    stringify guard lives in RdbmsClient.insert) - read the actual written row back from sqlite
    to verify what really landed in the column."""
    engine = DataMimicTest(project_dir, "test_entity_stringify_rdbms.xml", capture_test_result=True)
    engine.test_with_timer()

    db_files = list((project_dir / "db").glob("*.sqlite"))
    assert len(db_files) == 1, f"expected exactly one sqlite file, found {db_files}"
    with closing(sqlite3.connect(db_files[0])) as conn:
        name = conn.execute("SELECT name FROM t").fetchone()[0]

    assert isinstance(name, str)
    assert name.startswith("{") and "given_name" in name  # str(person.to_dict()), not a repr
