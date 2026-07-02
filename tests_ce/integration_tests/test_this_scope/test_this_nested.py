from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


def _run():
    engine = DataMimicTest(
        test_dir=Path(__file__).resolve().parent, filename="this_nested.xml", capture_test_result=True
    )
    engine.test_with_timer()
    return engine.capture_result()


def test_this_binds_to_current_scope_at_every_nesting_level():
    result = _run()
    companies = result["company"]
    assert len(companies) == 2

    for c in companies:
        # outermost <generate>: this = company scope
        assert c["c_self"] == c["cid"]

        # nestedKey(dict): this = dept scope (own sibling), and the flat outermost field stays visible
        dept = c["dept"]
        assert dept["d_self"] == dept["did"]
        assert dept["d_from_company"] == c["cbase"]

        # deeper nestedKey(dict): this = team scope; the outermost company field is still flat-visible
        team = dept["team"]
        assert team["t_self"] == team["tid"] == 99
        assert team["t_from_company"] == c["cbase"]

    # nested <generate> (list stream): this = each staff row's own scope
    staff = result["staff"]
    assert len(staff) == 4
    for s in staff:
        assert s["slabel"] == s["sidx"] * 1000  # this.sidx in a nested generate
        assert s["s_self"] == s["slabel"]  # this.slabel
