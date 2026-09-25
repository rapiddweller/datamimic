from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from datamimic_ce.data_mimic_test import DataMimicTest


def _descriptor(tmp_path: Path, *, target: str, count: int = 1, email: str | None = None) -> list[dict[str, object]]:
    email_key = f'<key name="email" constant="{email}"/>' if email is not None else ""
    path = tmp_path / "patients.xml"
    path.write_text(
        f"""<setup>
  <database id="db" dbms="sqlite" database="unique_id_target"/>
  <generate name="patients" count="{count}" pageSize="2" targetEntity="patients" target="{target}">
    <variable name="patient" entity="Patient" rngSeed="23"/>
    <key name="patient_id" script="patient.patient_id"/>
    <key name="status" constant="generated"/>
    {email_key}
  </generate>
</setup>
""",
        encoding="utf-8",
    )
    engine = DataMimicTest(test_dir=tmp_path, filename=path.name, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()["patients"]


def _create_target(tmp_path: Path) -> Path:
    db_dir = tmp_path / "db"
    db_dir.mkdir(exist_ok=True)
    database = db_dir / "unique_id_target.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE patients (patient_id TEXT PRIMARY KEY, status TEXT NOT NULL, email TEXT UNIQUE)"
        )
    return database


def _stored_rows(database: Path) -> list[tuple[str, str, str | None]]:
    with sqlite3.connect(database) as connection:
        return connection.execute("SELECT patient_id, status, email FROM patients ORDER BY patient_id").fetchall()


def test_seeded_target_output_matches_after_reset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    database = _create_target(tmp_path)

    first_capture = _descriptor(tmp_path, target="db", count=3)
    first_rows = _stored_rows(database)
    with sqlite3.connect(database) as connection:
        connection.execute("DELETE FROM patients")

    second_capture = _descriptor(tmp_path, target="db", count=3)
    second_rows = _stored_rows(database)

    assert second_capture == first_capture
    assert second_rows == first_rows


def test_insert_conflicting_with_existing_primary_key_fails_without_rekey(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    candidate_id = _descriptor(tmp_path, target="")[0]["patient_id"]
    database = _create_target(tmp_path)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO patients (patient_id, status, email) VALUES (?, 'existing', NULL)", (candidate_id,)
        )

    with pytest.raises(ValueError, match="UNIQUE constraint failed"):
        _descriptor(tmp_path, target="db")

    assert _stored_rows(database) == [(candidate_id, "existing", None)]


def test_explicit_upsert_updates_row_by_primary_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    candidate_id = _descriptor(tmp_path, target="")[0]["patient_id"]
    database = _create_target(tmp_path)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO patients (patient_id, status, email) VALUES (?, 'existing', NULL)", (candidate_id,)
        )

    _descriptor(tmp_path, target="db.upsert")

    assert _stored_rows(database) == [(candidate_id, "generated", None)]


def test_upsert_does_not_match_a_non_primary_unique_column(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    database = _create_target(tmp_path)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO patients (patient_id, status, email) VALUES ('existing-id', 'existing', 'same@example.test')"
        )

    with pytest.raises(IntegrityError, match="UNIQUE constraint failed"):
        _descriptor(tmp_path, target="db.upsert", email="same@example.test")

    assert _stored_rows(database) == [("existing-id", "existing", "same@example.test")]
