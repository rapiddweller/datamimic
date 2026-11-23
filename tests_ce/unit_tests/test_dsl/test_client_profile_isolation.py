"""A connection profile belongs to the <database> that names it. A typo in the next client's environment must fail
instead of reading the profile of the client before it."""

from pathlib import Path

from datamimic_ce.engine.dsl.api import DatabaseStatement, DescriptorParser
from datamimic_ce.engine.io.api import load_connection_profile


def test_the_profile_of_one_database_does_not_reach_the_next(tmp_path: Path) -> None:
    (tmp_path / "conf").mkdir()
    (tmp_path / "conf" / "prod.env.properties").write_text("crm.db.database=prod.db\n", encoding="utf-8")
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text(
        '<setup><database id="src" system="crm" environment="prod" dbms="sqlite"/>'
        '<database id="dst" system="crm" environment="tset" dbms="sqlite"/></setup>',
        encoding="utf-8",
    )
    # Non-empty platform properties: before, the profile of "src" was written into this shared dict.
    setup = DescriptorParser.parse(
        descriptor, {"unrelated.key": "x"}, "production", profile_loader=load_connection_profile
    )
    models = {s.model.id: s.model for s in setup.sub_statements if isinstance(s, DatabaseStatement)}
    assert models["src"].database == "prod.db"
    assert models["dst"].database is None
