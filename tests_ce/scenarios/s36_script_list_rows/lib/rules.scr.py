# A list that a script binds stays the script's own list of plain dicts (#441).
LIMITS = [{"qty": 2}, {"qty": 5}]


def all_plain(rows):
    return all(type(row) is dict for row in rows)
