import random
from typing import get_type_hints

import pytest

from datamimic_ce.domains.shared.datasets.loader import read_weighted_records
from datamimic_ce.engine.io.data_sources.weighted_entity_data_source import WeightedEntityDataSource
from datamimic_ce.engine.io.files.readers import FileUtil


def test_weighted_entity_reads_string_cells_and_default_weight_column(tmp_path):
    csv_path = tmp_path / "people.wgt.ent.csv"
    csv_path.write_text('person id,name,weight\n001,"Doe, Jane",2.5\n', encoding="utf-8")

    source = WeightedEntityDataSource(csv_path, ",", random.Random(7))

    assert source.generate() == {"person id": "001", "name": "Doe, Jane"}


def test_weighted_entity_custom_weight_column_and_separator(tmp_path):
    csv_path = tmp_path / "entities.csv"
    csv_path.write_text("code;label;chance\n007;Seven;1\n", encoding="utf-8")

    source = WeightedEntityDataSource(
        csv_path, ";", random.Random(7), weight_column_name="chance"
    )

    assert source.generate() == {"code": "007", "label": "Seven"}


def test_weighted_csv_skips_rows_missing_weight_and_invalid_weight_raises(tmp_path):
    csv_path = tmp_path / "entities.csv"
    csv_path.write_text("id,weight\nmissing\nvalid,2\n", encoding="utf-8")

    assert FileUtil.read_csv_having_weight_column(csv_path, "weight") == ([2.0], [{"id": "valid"}])

    invalid_path = tmp_path / "invalid.csv"
    invalid_path.write_text("id,weight\nbad,nope\n", encoding="utf-8")
    with pytest.raises(ValueError):
        FileUtil.read_csv_having_weight_column(invalid_path, "weight")


def test_weighted_entity_selection_replays_seeded_sequence(tmp_path):
    csv_path = tmp_path / "entities.csv"
    csv_path.write_text("id,weight\na,1\nb,2\nc,3\n", encoding="utf-8")
    first = WeightedEntityDataSource(csv_path, ",", random.Random(81))
    second = WeightedEntityDataSource(csv_path, ",", random.Random(81))

    first_sequence = [first.generate() for _ in range(100)]
    second_sequence = [second.generate() for _ in range(100)]

    assert first_sequence == second_sequence
    assert [row["id"] for row in first_sequence[:12]] == [
        "c", "b", "c", "b", "c", "a", "b", "c", "c", "c", "b", "b"
    ]


def test_weighted_entity_never_selects_zero_weight_row(tmp_path):
    csv_path = tmp_path / "entities.csv"
    csv_path.write_text("id,weight\na,1\nb,2\nzero,0\n", encoding="utf-8")
    source = WeightedEntityDataSource(csv_path, ",", random.Random(81))

    assert {source.generate()["id"] for _ in range(100)} == {"a", "b"}


def test_weighted_entity_retains_row_aliasing_and_empty_pool_error(tmp_path):
    csv_path = tmp_path / "single.csv"
    csv_path.write_text("id,weight\none,1\n", encoding="utf-8")
    source = WeightedEntityDataSource(csv_path, ",", random.Random(1))

    assert source.generate() is source.generate()

    empty_path = tmp_path / "empty.csv"
    empty_path.write_text("id,weight\n", encoding="utf-8")
    with pytest.raises(IndexError):
        WeightedEntityDataSource(empty_path, ",", random.Random(1)).generate()


def test_weighted_entity_all_zero_weights_keep_random_choices_error(tmp_path):
    csv_path = tmp_path / "zero.csv"
    csv_path.write_text("id,weight\na,0\nb,0\n", encoding="utf-8")
    source = WeightedEntityDataSource(csv_path, ",", random.Random(1))

    with pytest.raises(ValueError, match="greater than zero"):
        source.generate()


def test_domain_weighted_records_consumer_keeps_record_shape(tmp_path):
    csv_path = tmp_path / "domain.csv"
    csv_path.write_text("account,kind,probability\n00042,checking,3\n", encoding="utf-8")

    weights, records = read_weighted_records(csv_path, "probability")

    assert weights == [3.0]
    assert records == [{"account": "00042", "kind": "checking"}]


def test_weighted_entity_generate_return_type_is_explicit():
    assert get_type_hints(WeightedEntityDataSource.generate).get("return") == dict[str, str]
