from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest


def _run():
    engine = DataMimicTest(test_dir=Path(__file__).resolve().parent, filename="entity_field_compat.xml",
                           capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()["g"]


def test_legacy_camelcase_fields_resolve_and_expressions_work():
    rows = _run()
    assert len(rows) == 5
    assert all(r["given"] and r["house"] and r["bday"] for r in rows)  # givenName/houseNumber/birthDate
    assert all(r["full"] == f"{r['given']} {r['full'].split(' ', 1)[1]}" for r in rows)  # expression evaluated


def test_entity_field_compat_seeded_reproducible():
    keys = ("given", "bday", "full", "house")
    first = [tuple(r[k] for k in keys) for r in _run()]
    second = [tuple(r[k] for k in keys) for r in _run()]
    assert first == second
