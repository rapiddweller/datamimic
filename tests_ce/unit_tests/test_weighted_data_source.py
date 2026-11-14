from __future__ import annotations

from pathlib import Path
from random import Random
from typing import get_type_hints

import pytest

from datamimic_ce.engine.io.data_sources.weighted_data_source import WeightedDataSource
from datamimic_ce.engine.io.files.readers import FileUtil


class _CountingRandom(Random):
    def __init__(self, seed: int):
        super().__init__(seed)
        self.choices_calls = 0

    def choices(self, population, weights=None, *, cum_weights=None, k=1):
        self.choices_calls += 1
        return super().choices(population, weights=weights, cum_weights=cum_weights, k=k)


class _FixedResultRandom(Random):
    def __init__(self, value: object):
        super().__init__(0)
        self.value = value

    def choices(self, population, weights=None, *, cum_weights=None, k=1):
        return [self.value]


class _StringSubclass(str):
    pass


@pytest.mark.parametrize(
    ("separator", "contents", "expected"),
    [
        (",", "value,weight\n001,1\ntrue,1\n,1\nfalse,1\n\n", ["001", "true", "", "false", None]),
        ("|", "001|1\nfalse|1\n", ["001", "false"]),
    ],
    ids=["comma-headered-text-empty-and-missing", "pipe-headerless-text"],
)
def test_generate_keeps_real_csv_text_empty_and_missing_values(
    tmp_path: Path, separator: str, contents: str, expected: list[str | None]
) -> None:
    source_file = tmp_path / "values.wgt.csv"
    source_file.write_text(contents, encoding="utf-8")

    class ChooseInOrder(Random):
        def __init__(self):
            super().__init__(0)
            self.calls = 0

        def choices(self, population, weights=None, *, cum_weights=None, k=1):
            value = population[self.calls]
            self.calls += 1
            return [value]

    rng = ChooseInOrder()
    source = WeightedDataSource(source_file, separator, rng)
    actual = [source.generate() for _ in expected]

    assert actual == expected
    assert all(value is None or type(value) is str for value in actual)
    assert rng.calls == len(expected)


def test_generate_uses_one_seeded_choices_draw_per_value_and_preserves_rng_state(tmp_path: Path) -> None:
    source_file = tmp_path / "weighted.wgt.csv"
    source_file.write_text(
        "value|weight\n001|0\ntrue|1\n|1\nfalse|2\ndup|1\ndup|1\nmissing-weight\n\n",
        encoding="utf-8",
    )
    draw_count = 40
    seed = 718
    df = FileUtil.read_weight_csv(source_file, "|")
    expected_rng = Random(seed)
    expected = [expected_rng.choices(list(df[0]), weights=list(df[1]), k=1)[0] for _ in range(draw_count)]

    actual_rng = _CountingRandom(seed)
    source = WeightedDataSource(source_file, "|", actual_rng)
    actual = [source.generate() for _ in range(draw_count)]

    assert actual == expected
    assert actual_rng.getstate() == expected_rng.getstate()
    assert actual_rng.choices_calls == draw_count
    assert "001" not in actual
    assert all(value is None or isinstance(value, str) for value in actual)


@pytest.mark.parametrize(
    "value",
    [None, _StringSubclass("subclass text")],
    ids=["none", "string-subclass"],
)
def test_generate_returns_valid_choice_without_coercion_or_copy(tmp_path: Path, value: object) -> None:
    source_file = tmp_path / "one-value.wgt.csv"
    source_file.write_text("base,1\n", encoding="utf-8")

    result = WeightedDataSource(source_file, ",", _FixedResultRandom(value)).generate()

    assert result is value


@pytest.mark.parametrize(
    "value",
    [7, 7.5, ["not", "text"], object()],
    ids=["integer", "float", "list", "arbitrary-object"],
)
def test_generate_rejects_non_text_choice_as_wrapped_type_error(tmp_path: Path, value: object) -> None:
    source_file = tmp_path / "one-value.wgt.csv"
    source_file.write_text("valid,1\n", encoding="utf-8")
    source = WeightedDataSource(source_file, ",", _FixedResultRandom(value))

    with pytest.raises(ValueError, match=r"\[E006/I102\] .*'[a-z-]*\.wgt\.csv'") as raised:
        source.generate()

    assert type(raised.value.__cause__) is TypeError
    assert str(raised.value.__cause__) == "Weighted CSV values must be strings or None"


def test_generate_exposes_exact_public_return_type() -> None:
    assert get_type_hints(WeightedDataSource.generate)["return"] == str | None


def test_empty_weights_fail_on_generate_with_original_index_error(tmp_path: Path) -> None:
    source_file = tmp_path / "empty.wgt.csv"
    source_file.write_text("", encoding="utf-8")
    source = WeightedDataSource(source_file, ",", Random(1))

    with pytest.raises(ValueError, match=r"\[E006/I102\] .*'[a-z-]*\.wgt\.csv'") as raised:
        source.generate()

    assert type(raised.value.__cause__) is IndexError
    assert str(raised.value.__cause__) == "list index out of range"


def test_all_zero_weights_fail_on_generate_with_original_random_error(tmp_path: Path) -> None:
    source_file = tmp_path / "all-zero.wgt.csv"
    source_file.write_text("A,0\nB,0\n", encoding="utf-8")
    source = WeightedDataSource(source_file, ",", Random(1))

    with pytest.raises(ValueError, match=r"\[E006/I102\] .*'[a-z-]*\.wgt\.csv'") as raised:
        source.generate()

    assert type(raised.value.__cause__) is ValueError
    assert str(raised.value.__cause__) == "Total of weights must be finite"


@pytest.mark.parametrize(
    ("separator", "contents"),
    [
        ("|", "A|1\nB|not-a-number\n"),
        ("|", "OPERATOR|90\nSECRET-A|\n"),
        ("|", "SECRET-A|\nB|3\n"),
        (",", "SECRET-A|90\nB|10\n"),
        ("|", "SECRET-A\nB\n"),
        ("|", "SECRET-A|1|x\n"),
    ],
    ids=[
        "non-number-weight",
        "empty-weight-later-line",
        "empty-weight-first-line",
        "separator-does-not-split",
        "no-weight-column",
        "third-column",
    ],
)
def test_malformed_weighted_file_fails_with_the_typed_error_that_names_only_the_file(
    tmp_path: Path, separator: str, contents: str
) -> None:
    """#448: the typed I102 at construction, never a raw pandas error; no value and no host path in the message."""
    source_file = tmp_path / "roles.wgt.csv"
    source_file.write_text(contents, encoding="utf-8")

    with pytest.raises(ValueError, match=r"\[E006/I102\] .*'roles\.wgt\.csv'") as raised:
        WeightedDataSource(source_file, separator, Random(1))

    assert type(raised.value.__cause__) is ValueError
    assert "SECRET-A" not in str(raised.value)
    assert str(tmp_path) not in str(raised.value)


def test_a_first_line_with_a_named_weight_stays_a_header(tmp_path: Path) -> None:
    source_file = tmp_path / "roles.wgt.csv"
    source_file.write_text("role|weight\nA|3\nB|\n", encoding="utf-8")

    with pytest.raises(ValueError, match=r"\[E006/I102\]"):  # the header is skipped, the empty weight of B is not
        FileUtil.read_weight_csv(source_file, "|")
    valid_file = tmp_path / "valid.wgt.csv"  # the reader caches file content by path
    valid_file.write_text("role|weight\nA|3\nB|1\n", encoding="utf-8")
    assert FileUtil.read_weight_csv(valid_file, "|")[0].tolist() == ["A", "B"]
