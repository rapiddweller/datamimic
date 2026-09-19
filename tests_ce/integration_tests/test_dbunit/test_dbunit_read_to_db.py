import shutil
from pathlib import Path

from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.connection_config.rdbms_connection_config import RdbmsConnectionConfig
from datamimic_ce.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent


def test_ragged_dbunit_table_inserts_into_a_real_rdbms():
    # THE real use case: read a dbunit table (ragged parent_id) and INSERT into a DB. Column unification
    # (absent -> NULL) means the batch insert sees a uniform column set instead of crashing.
    shutil.rmtree(_DIR / "db", ignore_errors=True)
    try:
        DataMimicTest(test_dir=_DIR, filename="read_to_db.xml", capture_test_result=True).test_with_timer()
        cfg = RdbmsConnectionConfig(dbms="sqlite", database="dbunit_read_db", host=None, port=None,
                                    user=None, password=None, db_schema=None)
        client = RdbmsClient(cfg, task_id="t")
        assert client.get("SELECT COUNT(*) FROM db_category")[0][0] == 28
        # a top-level category landed with NULL parent_id
        assert client.get("SELECT COUNT(*) FROM db_category WHERE parent_id IS NULL")[0][0] >= 1
    finally:
        shutil.rmtree(_DIR / "db", ignore_errors=True)
