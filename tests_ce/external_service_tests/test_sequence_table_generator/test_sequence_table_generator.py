# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import text

from datamimic_ce.engine.dsl.vocabulary.enums.dbms_enums import Dbms
from datamimic_ce.engine.io.api import load_connection_profile
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig
from datamimic_ce.engine.runtime.api import create_run_session
from datamimic_ce.engine.runtime.contracts import RunRequest
from datamimic_ce.engine.runtime.lifecycle.config import get_settings
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


@pytest.mark.parametrize(("dbms", "cached"), [(Dbms.POSTGRESQL, False), (Dbms.POSTGRESQL, True), (Dbms.MYSQL, False)])
def test_concurrent_sequence_reservations(dbms, cached):
    """Two independent sessions allocate from one counter with and without pre_execute."""
    directory = Path(__file__).resolve().parent
    environment = "local" if get_settings().RUNTIME_ENVIRONMENT == "development" else "environment"
    profile = load_connection_profile(directory.parent / "test_rdbms_sql_matrix", environment)
    prefix = dbms.value + ".db."
    reservation_profile = {
        key.replace(prefix, "reservation.db.", 1): value for key, value in profile.items() if key.startswith(prefix)
    }
    writer = RdbmsClient(
        RdbmsConnectionConfig(
            dbms=dbms,
            host=profile[prefix + "host"],
            port=int(profile[prefix + "port"]),
            database=profile[prefix + "database"],
            user=profile[prefix + "user"],
            password=profile[prefix + "password"],
            db_schema=None,
        )
    )
    table = "ce_seq_" + uuid4().hex[:16]
    sequence = table + "_id_seq"
    starting_barrier = Barrier(2)

    def run():
        session = create_run_session(
            RunRequest(
                descriptor_path=directory / "concurrent_reservations.xml",
                platform_props={"sequence_table": table},
                profile_loader=lambda _directory, _environment: reservation_profile,
                test_mode=True,
            )
        )
        starting_barrier.wait(timeout=10)
        captured = session.execute().captured
        assert captured["empty"] == []
        prepared = [row["id"] for row in captured["prepared"]]
        lazy = [row["id"] for row in captured["lazy"]]
        assert len(prepared) == 13 and len(lazy) == 5
        assert prepared == list(range(prepared[0], prepared[0] + 13))
        assert lazy == list(range(lazy[0], lazy[0] + 5))
        return prepared + lazy

    try:
        minimum = 1
        if dbms is Dbms.MYSQL:
            writer.execute_sql_script(
                f"CREATE TABLE {table} (id BIGINT AUTO_INCREMENT PRIMARY KEY) ENGINE=InnoDB AUTO_INCREMENT=500"
            )
            minimum = 500
        elif cached:
            # This backend caches 500..563. Reuse the same pooled backend for a reservation
            # so a nextval()-based implementation would see 501, below the shared boundary.
            writer.execute_sql_script(f"CREATE SEQUENCE public.{sequence} START WITH 500 CACHE 64")
            with writer.engine.begin() as connection:
                assert (
                    connection.execute(text("SELECT nextval(CAST(:seq AS regclass))"), {"seq": sequence}).scalar()
                    == 500
                )
            assert writer.reserve_sequence_block(sequence, 3) == 564
            minimum = 567

        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(run)
            second = executor.submit(run)
            ids = first.result() + second.result()
        assert len(ids) == len(set(ids)) == 36
        assert min(ids) == minimum
    finally:
        if dbms is Dbms.POSTGRESQL:
            writer.execute_sql_script(f"DROP SEQUENCE IF EXISTS public.{sequence}")
        else:
            writer.execute_sql_script(f"DROP TABLE IF EXISTS {table}")
        if writer.engine is not None:
            writer.engine.dispose()


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
        """Check unique ids when one MySQL run mixes explicit reservations and default inserts."""
        engine = DataMimicTest(test_dir=self._test_dir, filename="mysql_test.xml", capture_test_result=True)
        engine.test_with_timer()
        result = engine.capture_result()

        ids = [row["id"] for row in result["check"]]
        assert len(ids) == len(set(ids)), f"duplicate ids: {ids}"

    def test_sequence_table_generator_postgres_uneven_multiprocess(self):
        """Edge case: count=13 does not divide evenly across numProcess=4 (13 = 4+4+4+1).
        Workers' id ranges must stay apart: no duplicate ids, and pre_execute() reserves the same
        rounded-up per_process_count * total_processes block __init__ assumed."""
        engine = DataMimicTest(
            test_dir=self._test_dir, filename="postgresql_uneven_mp_test.xml", capture_test_result=True
        )
        engine.test_with_timer()
        result = engine.capture_result()

        ids = [row["id"] for row in result["check"]]
        assert len(ids) == 13
        assert len(set(ids)) == 13, f"duplicate ids: {ids}"

    @pytest.mark.parametrize("filename", ["postgresql_paged_test.xml", "postgresql_paged_mp_test.xml"])
    def test_sequence_table_generator_postgres_count_above_page_size(self, filename):
        """count=13 with pageSize=3: every page continues the sequence (a cached generator used
        to be served exhausted to later pages, losing rows) and the skip applies once."""
        engine = DataMimicTest(test_dir=self._test_dir, filename=filename, capture_test_result=True)
        engine.test_with_timer()
        ids = [row["id"] for row in engine.capture_result()["check"]]
        assert len(ids) == 13
        assert max(ids) - min(ids) == 12, f"non-contiguous ids: {sorted(ids)}"

    def test_sequence_table_generator_mysql_uneven_multiprocess(self):
        """MySQL SequenceTableGenerator gracefully degrades to single-process
        (PR #217 added _uses_mysql_sequence policy).  The run must complete with
        a gapless, duplicate-free sequence despite the numProcess=4 request."""
        engine = DataMimicTest(test_dir=self._test_dir, filename="mysql_uneven_mp_test.xml", capture_test_result=True)
        engine.test_with_timer()
        result = engine.capture_result()
        ids = [row["id"] for row in result["check"]]
        assert len(ids) == 13
        assert len(set(ids)) == 13, f"duplicate ids: {ids}"
        # The table may carry state from prior test runs; only assert
        # contiguousness and coverage, not the absolute starting value.
        assert max(ids) - min(ids) == 12, f"non-contiguous ids: {sorted(ids)}"

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
