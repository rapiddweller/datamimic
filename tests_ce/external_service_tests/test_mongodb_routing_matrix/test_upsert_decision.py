# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.
"""MongoDB upsert insert-vs-update, end to end against a live mongo (external-service shard).

``upsert_decision.xml`` is also run against an in-memory collection by
``tests_ce/unit_tests/test_mongo_upsert_descriptor.py``, which imports ``check_classes`` from here."""

from pathlib import Path

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def check_classes(result: dict) -> None:
    """One outcome per equivalence class of the descriptor."""
    tags = {name: [row["tag"] for row in rows] for name, rows in result.items() if name.startswith("check_")}
    assert tags["check_new"] == ["new"], "insert of a new document"
    assert tags["check_upd"] == ["updated", "updated"], "update of existing documents, none inserted"
    assert tags["check_call_sel"] == ["call"], "mongodb.upsert() with a selector source"
    assert tags["check_space_sel"] == ["space"], "mongodb . upsert with a selector source"
    assert tags["check_plain_type"] == ["plain"], "mongodb.upsert with a type source"
    assert tags["check_call_type"] == ["call"], "mongodb.upsert() with a type source"
    assert tags["check_space_type"] == ["space"], "mongodb . upsert with a type source"
    assert tags["check_ctl_delete"] == [], "control: delete target writes nothing"
    assert tags["check_ctl_insert"] == [], "control: plain insert target writes nothing"


def test_upsert_decision_classes() -> None:
    engine = DataMimicTest(test_dir=_TEST_DIR, filename="upsert_decision.xml", capture_test_result=True)
    engine.test_with_timer()
    check_classes(engine.capture_result())
