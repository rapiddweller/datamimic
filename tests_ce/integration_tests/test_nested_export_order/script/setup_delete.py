# Same rationale as setup_insert.py for building this via a raw sqlite3 connection
# (executescript) rather than <execute type="sql">: the naive ";" split in RdbmsClient.
# execute_sql_script cannot run a CREATE TRIGGER body for sqlite.
#
# Two triggers enforce the FK in both directions across the two phases that share this db file:
#   - fk_orders_user (BEFORE INSERT on orders): phase 1 must insert the parent user before its
#     child orders - proves the existing parent-before-child insert order still holds.
#   - fk_users_children (BEFORE DELETE on users): phase 2 must delete a user's orders before the
#     user row itself - this is what the new delete-first ordering (TaskUtil.export_product_by_page)
#     is proving.
import sqlite3
from pathlib import Path

_db_path = Path("db") / "nested_delete_db.sqlite"
_db_path.parent.mkdir(parents=True, exist_ok=True)
_conn = sqlite3.connect(str(_db_path))
_conn.executescript(
    """
    DROP TRIGGER IF EXISTS fk_orders_user;
    DROP TRIGGER IF EXISTS fk_users_children;
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

    CREATE TRIGGER fk_users_children
    BEFORE DELETE ON users
    BEGIN
        SELECT RAISE(ABORT, 'FK: children exist')
        WHERE EXISTS (SELECT 1 FROM orders WHERE user_id = OLD.id);
    END;
    """
)
_conn.commit()
_conn.close()
