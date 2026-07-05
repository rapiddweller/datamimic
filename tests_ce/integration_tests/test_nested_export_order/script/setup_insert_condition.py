# Same fixture as setup_insert.py (see its comment for why this is built via a raw sqlite3
# connection rather than <execute type="sql">), on its own db file so this scenario - a nested
# <generate> wrapped in <condition><if> - doesn't share state with the plain nesting test.
import sqlite3
from pathlib import Path

_db_path = Path("db") / "nested_insert_cond_db.sqlite"
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
