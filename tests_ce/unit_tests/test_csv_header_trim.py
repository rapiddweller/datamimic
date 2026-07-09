# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.utils.file_util import FileUtil


def test_csv_header_whitespace_is_stripped(tmp_path):
    # a padded/aligned CSV (migrated legacy entity CSVs look like this) must yield clean column keys,
    # so a script field access like this.name resolves.
    f = tmp_path / "padded.csv"
    f.write_text("ean_code     ,name              ,price\n8000353006386,Limoncello,9.85\n")
    rows = FileUtil.read_csv_to_dict_list(f, ",")
    assert rows == [{"ean_code": "8000353006386", "name": "Limoncello", "price": "9.85"}]
    assert "name" in rows[0] and "name              " not in rows[0]
