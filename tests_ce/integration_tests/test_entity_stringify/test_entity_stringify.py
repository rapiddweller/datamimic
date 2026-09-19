# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Binding a whole entity (<key script="person">) into a scalar RDBMS column - migration parity
(the legacy toString()). Confirmed empirically before this fix: sqlite3.ProgrammingError,
'type Person is not supported' - so this is a pure improvement, not a behavior change with
regression risk (nothing succeeds today for this input)."""

import shutil
import sqlite3
from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_dir = Path(__file__).resolve().parent


def test_entity_stringify_rdbms():
    """capture_result() reflects the generated record BEFORE export-time normalization (the
    stringify guard lives in RdbmsClient.insert) - read the actual written row back from sqlite
    to verify what really landed in the column."""
    db_dir = _dir / "db"
    repo_root_db_dir = _dir.parents[2] / "db"
    for d in (db_dir, repo_root_db_dir):
        shutil.rmtree(d, ignore_errors=True)
    try:
        engine = DataMimicTest(_dir, "test_entity_stringify_rdbms.xml", capture_test_result=True)
        engine.test_with_timer()

        db_files = list(repo_root_db_dir.glob("*.sqlite")) if repo_root_db_dir.is_dir() else []
        db_files += list(db_dir.glob("*.sqlite")) if db_dir.is_dir() else []
        assert len(db_files) == 1, f"expected exactly one sqlite file, found {db_files}"
        conn = sqlite3.connect(db_files[0])
        try:
            name = conn.execute("SELECT name FROM t").fetchone()[0]
        finally:
            conn.close()

        assert isinstance(name, str)
        assert name.startswith("{") and "given_name" in name  # str(person.to_dict()), not a repr
    finally:
        for d in (db_dir, repo_root_db_dir):
            shutil.rmtree(d, ignore_errors=True)
