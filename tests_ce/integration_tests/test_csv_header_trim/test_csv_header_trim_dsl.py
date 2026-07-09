# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""CSV header whitespace trim, end to end: a padded/aligned CSV (Benerator entity-CSV style)
must yield clean column KEYS so script field access resolves - while cell VALUES keep their
whitespace untouched (trimming values would corrupt data; only the keys are structural)."""

from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest

_dir = Path(__file__).resolve().parent


def test_padded_headers_resolve_in_scripts_and_values_stay_untouched():
    engine = DataMimicTest(_dir, "test_header_trim.xml", capture_test_result=True)
    engine.test_with_timer()
    rows = engine.capture_result()["products"]
    assert len(rows) == 2

    # happy path: the padded "name              " header is accessible as this.name
    assert rows[0]["clean_name"] == "Limoncello"
    # keys are clean on the record itself too
    assert {"ean_code", "name", "price"} <= set(rows[0])
    assert not any(k != k.strip() for row in rows for k in row)

    # edge (contract boundary): VALUES are not trimmed - "Mango Chutney   " keeps its padding
    assert rows[1]["clean_name"] == "Mango Chutney   "
