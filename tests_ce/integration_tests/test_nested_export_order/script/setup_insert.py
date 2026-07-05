# FK enforcement without a real RDBMS: a BEFORE INSERT trigger raises (ABORT) if a child
# row's parent is missing. If the engine ever wrote a nested <generate>'s rows before its
# parent's, this trigger fires and the run aborts - that is the whole proof mechanism.
#
# Built via a raw sqlite3 connection (executescript), NOT <execute type="sql">: RdbmsClient.
# execute_sql_script splits scripts on a bare ";" for sqlite (datamimic_ce/clients/rdbms_client.py),
# which breaks on the trigger body's internal ";" before END. executescript handles multi-statement
# scripts (including trigger bodies) correctly, and targets the exact same file
# RdbmsClient opens afterwards: db/<database>.sqlite, relative to CWD (RUNTIME_ENVIRONMENT is always
# "development" or "production" - see datamimic_ce/config.py - so RdbmsClient always resolves the
# sqlite path that way).
import sqlite3
from pathlib import Path

_db_path = Path("db") / "nested_insert_db.sqlite"
_db_path.parent.mkdir(parents=True, exist_ok=True)
_conn = sqlite3.connect(str(_db_path))
_conn.executescript(
    """
    DROP TRIGGER IF EXISTS fk_orders_user;
    DROP TABLE IF EXISTS orders;
    DROP TABLE IF EXISTS users;

    CREATE TABLE users (id INTEGER PRIMARY KEY);
    CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, seq INTEGER);

    CREATE TRIGGER fk_orders_user
    BEFORE INSERT ON orders
    BEGIN
        SELECT RAISE(ABORT, 'FK: parent missing')
        WHERE NOT EXISTS (SELECT 1 FROM users WHERE id = NEW.user_id);
    END;
    """
)
_conn.commit()
_conn.close()
