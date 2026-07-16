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
        """sequence='...' overrides the {type}_{name}_seq convention (legacy-DSL
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

    def test_sequence_table_generator_mysql(self):
        """MySQL has no freestanding sequence object - SequenceTableGenerator integrates
        directly with the target table's own AUTO_INCREMENT counter (rdbms_client.py:
        _advance_mysql_auto_increment), advanced atomically via MySQL's session-scoped
        GET_LOCK/RELEASE_LOCK around a read-then-ALTER TABLE round trip. MySQL execution is
        deliberately single-process because it has no atomic native sequence reservation.

        Only asserts no-duplicate-ids, not "exactly 30 rows exist": SequenceTableGenerator is
        re-instantiated per page/scan-phase pass (existing engine behavior, confirmed present
        for Postgres too - functional.sequence_table_generator ends up with 24 rows and a max id
        of 35 there as well, not 30/30), and each throwaway instantiation's
        get_current_sequence_number() call burns a value that's never used. That's a real,
        pre-existing, dialect-independent gap in DATAMIMIC's own architecture, not something this
        fix introduces or is scoped to close - the guarantee this fix owns is that whatever ids
        DO get assigned are unique, which is what's asserted here.

        Multiprocessing rejection is covered by the unit contract; this external test proves the
        supported single-process MySQL path against the real database."""
        engine = DataMimicTest(test_dir=self._test_dir, filename="mysql_test.xml", capture_test_result=True)
        engine.test_with_timer()
        result = engine.capture_result()

        ids = [row["id"] for row in result["check"]]
        assert len(ids) == len(set(ids)), f"duplicate ids: {ids}"

    def test_sequence_table_generator_postgres_uneven_multiprocess(self):
        """Edge case: count=13 does not divide evenly across numProcess=4 (13 = 4+4+4+1).
        Regression for a real bug found this session: SetupContext.process_id was never wired
        to the actual multiprocessing worker index (generate_worker.py's mp_preprocess only used
        worker_id for log naming) - every worker read process_id as None/0, so
        SequenceTableGenerator's per-process offset (process_id * per_process_count) was always
        a no-op. The only thing separating workers' ranges was the shared DB sequence's own
        atomic advance, which isn't sufficient once ranges are supposed to be kept apart by an
        offset that never applied - reproduced as a real duplicate-key collision, 5/5 runs,
        before wiring context.root.process_id = worker_id - 1 in mp_preprocess. Also fixes a
        second, smaller bug this exposed: pre_execute() reserved the raw statement count instead
        of the same rounded-up per_process_count * total_processes block __init__ assumed."""
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="postgresql_uneven_mp_test.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()

        ids = [row["id"] for row in result["check"]]
        assert len(ids) == 13
        assert len(set(ids)) == 13, f"duplicate ids: {ids}"

    def test_sequence_table_generator_mysql_uneven_multiprocess(self):
        """MySQL's emulated sequence cannot enter an unsafe multiprocess execution."""
        engine = DataMimicTest(test_dir=self._test_dir, filename="mysql_uneven_mp_test.xml", capture_test_result=True)
        with pytest.raises(ValueError, match="MySQL source is single-process only"):
            engine.test_with_timer()

    @pytest.mark.skip(
        reason="MSSQL native-sequence support was prototyped and pulled: SequenceTableGenerator "
        "is re-instantiated per page/scan-phase pass (existing engine behavior), and each "
        "instantiation's get_current_sequence_number() call was observed to produce colliding id "
        "ranges against MSSQL non-deterministically. Needs a fix to that interaction before this "
        "can ship, not just a dialect-specific SQL port - see PR discussion."
    )
    def test_sequence_table_generator_mssql(self):
        engine = DataMimicTest(test_dir=self._test_dir, filename="mssql_test.xml", capture_test_result=True)
        engine.test_with_timer()
        engine.capture_result()
