# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest


class TestSequenceTableGenerator:
    _test_dir = Path(__file__).resolve().parent

    def test_sequence_table_generator_postgres(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="postgresql_test.xml", capture_test_result=True)
        engine.test_with_timer()
        engine.capture_result()

    def test_sequence_table_generator_postgres_explicit_sequence_name(self):
        """sequence='...' overrides the {type}_{name}_seq convention (Benerator
        DBSequenceGenerator parity): an unqualified explicit name lands in the credential
        schema, a schema-qualified one ('migrated_schema.legacy_seq') binds to the DBA
        pre-created sequence (START 500) instead of failing on a 3-part identifier or
        minting a fresh sequence at 1."""
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="postgresql_explicit_sequence_test.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()

        catalog = {row["seq"] for row in result["seq_catalog"]}
        assert "functional.custom_seq_name" in catalog
        assert "migrated_schema.legacy_seq" in catalog
        # The convention-derived names must NOT have been created for these keys
        assert not any("explicit_plain_id_seq" in s or "explicit_qualified_id_seq" in s for s in catalog)

        qualified_ids = [row["id"] for row in result["qualified_rows"]]
        assert len(qualified_ids) == 5
        # Pre-created at START 500: ids from the 500-region prove the existing sequence was
        # found and used, not a fresh one starting at 1.
        assert all(i >= 400 for i in qualified_ids), qualified_ids

        plain_ids = [row["id"] for row in result["plain_rows"]]
        assert len(plain_ids) == len(set(plain_ids)) == 5

    @pytest.mark.skip(reason="MySQL is not supported in this version")
    def test_sequence_table_generator_mysql(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="mysql_test.xml", capture_test_result=True)
        engine.test_with_timer()
        engine.capture_result()

    @pytest.mark.skip(reason="MSSQL is not supported in this version")
    def test_sequence_table_generator_mssql(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="mssql_test.xml", capture_test_result=True)
        engine.test_with_timer()
        engine.capture_result()
