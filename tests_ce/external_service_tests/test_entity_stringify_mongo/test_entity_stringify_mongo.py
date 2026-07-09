# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Binding a whole entity (<key script="person">) into a scalar Mongo field - migration parity
(the legacy toString()). Confirmed empirically before this fix: bson.errors.InvalidDocument (a
bare Person can't be BSON-encoded) - so this is a pure improvement, not a behavior change with
regression risk."""

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_dir = Path(__file__).resolve().parent


def test_entity_stringify_mongo():
    engine = DataMimicTest(_dir, "test_entity_stringify_mongo.xml", capture_test_result=True)
    engine.test_with_timer()
    rows = engine.capture_result()["check"]
    assert len(rows) == 1
    name = rows[0]["name"]
    assert isinstance(name, str)
    assert name.startswith("{") and "given_name" in name  # str(person.to_dict()), not a repr
