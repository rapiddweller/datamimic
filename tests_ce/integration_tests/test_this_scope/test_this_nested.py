from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


def _run():
    engine = DataMimicTest(
        test_dir=Path(__file__).resolve().parent, filename="this_nested.xml", capture_test_result=True
    )
    engine.test_with_timer()
    return engine.capture_result()


def test_scope_aliases_bind_at_every_nesting_level():
    companies = _run()["company"]
    assert len(companies) == 2

    for c in companies:
        # outermost <generate>: this and root both point at the top scope
        assert c["c_self"] == c["cid"]  # this.cid
        assert c["c_root"] == c["cid"]  # root.cid

        # nestedKey(dict): this = dept scope, parent = company, root = outermost company
        dept = c["dept"]
        assert dept["d_self"] == dept["did"]  # this.did
        assert dept["d_parent"] == c["cbase"]  # parent.cbase (company)
        assert dept["d_root"] == c["cbase"]  # root.cbase

        # deeper nestedKey(dict): this = team, parent = dept, root = outermost company
        team = dept["team"]
        assert team["t_self"] == team["tid"] == 99  # this.tid
        assert team["t_parent"] == dept["did"]  # parent.did (dept)
        assert team["t_root"] == c["cid"]  # root.cid (company)
