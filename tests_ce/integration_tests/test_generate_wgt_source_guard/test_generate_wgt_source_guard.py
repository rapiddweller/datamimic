# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""<generate source="x.wgt.csv"> (the value|weight format) only raises when the file is
HEADERLESS - the plain CSV reader has no coherent way to read that at all, it would treat the
first data row as a header, producing nonsense column names and one fewer row than the file has.
A HEADERED ".wgt.csv" (FileUtil.read_weight_csv now accepts either, see feat/wgt-csv-header-
optional) falls through to the plain CSV reader instead: reading it plainly (ignoring the weight,
no resampling) is coherent, just unweighted.

<generate source="x.wgt.ent.csv"> draws `count` rows by the weights of its weightColumn, with replacement,
as EE does (#452). It needs weightColumn and count, and refuses what the draw would ignore."""

from pathlib import Path

import pytest

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_dir = Path(__file__).resolve().parent


def test_generate_source_wgt_csv_headerless_raises():
    engine = DataMimicTest(_dir, "generate_wgt_plain.xml", capture_test_result=True)
    with pytest.raises(ValueError, match=r"\.wgt\.csv"):
        engine.test_with_timer()


def test_generate_source_wgt_csv_with_header_reads_as_plain_csv():
    """A headered '.wgt.csv' is NOT weighted (no resampling, no bias toward the higher-weight
    row) - just an ordinary headered CSV read, weight column included as literal data. Must NOT
    raise, unlike the headerless case."""
    engine = DataMimicTest(_dir, "generate_wgt_with_header.xml", capture_test_result=True)
    engine.test_with_timer()
    rows = engine.capture_result()["rows"]
    assert {row["value"] for row in rows} <= {"true", "false"}
    assert all("weight" in row for row in rows)


def _run_inline(tmp_path, setup: str, products: str = "id,name,weight\n1,Cheap,80\n2,Expensive,20\n"):
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "data" / "products.wgt.ent.csv").write_text(products, encoding="utf-8")
    (tmp_path / "datamimic.xml").write_text(setup, encoding="utf-8")
    engine = DataMimicTest(tmp_path, "datamimic.xml", capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()["rows"]


def test_generate_source_wgt_ent_csv_draws_by_weight_without_the_weight_column():
    engine = DataMimicTest(_dir, "generate_wgt_ent.xml", capture_test_result=True)
    engine.test_with_timer()
    rows = engine.capture_result()["rows"]
    assert len(rows) == 200
    assert all(set(row) == {"id", "name"} for row in rows)
    cheap = sum(row["name"] == "Cheap" for row in rows)
    assert 130 <= cheap <= 190  # weight 80 of 100: a plain read would give exactly 100


@pytest.mark.parametrize("workers", ["1", "2"])
def test_generate_source_wgt_ent_csv_replays_with_a_seed(tmp_path, workers):
    def draw(seed: int):
        setup = (
            f'<setup rngSeed="{seed}" multiprocessing="False">'
            '<generate name="rows" source="data/products.wgt.ent.csv" separator="," '
            f'weightColumn="weight" count="40" pageSize="{int(workers) * 7}" target="JSON"/></setup>'
        )
        return _run_inline(tmp_path, setup)

    first = draw(7)
    assert first == draw(7)
    assert first != draw(8)


@pytest.mark.parametrize(
    "attributes,issue,text",
    [
        ('count="5"', "I983", "weightColumn"),
        ('weightColumn="weight"', "I983", "count"),
        ('weightColumn="weight" count="5" distribution="ordered"', "I983", "distribution"),
        ('weightColumn="weight" count="5" cyclic="true"', "I983", "cyclic"),
        ('weightColumn="weight" count="5" unique="true"', "I983", "unique"),
        ('weightColumn="weight" count="5" where="True"', "I983", "where"),
        ('weightColumn="weights" count="5"', "I865", "weights"),
    ],
)
def test_generate_source_wgt_ent_csv_refuses_what_the_draw_cannot_honor(tmp_path, attributes, issue, text):
    setup = (
        '<setup><generate name="rows" source="data/products.wgt.ent.csv" separator="," '
        f'{attributes} target="JSON"/></setup>'
    )
    with pytest.raises(Exception, match=text) as caught:
        _run_inline(tmp_path, setup)
    assert caught.value.issue_code.value == issue


@pytest.mark.parametrize(
    "products,issue",
    [
        ("id,name,weight\n", "I867"),
        ("id,name,weight\n1,Cheap,0\n", "I868"),
        ("id,name,weight\n1,Cheap,x\n", "I868"),
        ("id,name,weight\n1,Cheap,nan\n", "I868"),
    ],
)
def test_generate_source_wgt_ent_csv_refuses_unusable_weights(tmp_path, products, issue):
    setup = (
        '<setup><generate name="rows" source="data/products.wgt.ent.csv" separator="," '
        'weightColumn="weight" count="5" target="JSON"/></setup>'
    )
    with pytest.raises(Exception) as caught:
        _run_inline(tmp_path, setup, products)
    assert caught.value.issue_code.value == issue


def test_generate_weight_column_on_another_source_is_refused(tmp_path):
    setup = (
        '<setup><generate name="rows" source="data/products.ent.csv" separator="," '
        'weightColumn="weight" count="1" target="JSON"/></setup>'
    )
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "products.ent.csv").write_text("id,name,weight\n1,Cheap,80\n", encoding="utf-8")
    (tmp_path / "datamimic.xml").write_text(setup, encoding="utf-8")
    with pytest.raises(Exception, match="weightColumn") as caught:
        DataMimicTest(tmp_path, "datamimic.xml", capture_test_result=True).test_with_timer()
    assert caught.value.issue_code.value == "I983"
