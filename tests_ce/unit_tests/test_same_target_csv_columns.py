# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import csv
from pathlib import Path

import pytest

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


@pytest.mark.parametrize("same_order", [True, False])
def test_conditional_children_share_csv_header_order(tmp_path: Path, same_order: bool) -> None:
    a = '<key name="a" constant="A"/>'
    b = '<key name="b" constant="B"/>'
    (tmp_path / "branches.xml").write_text(
        '<setup multiprocessing="0"><generate name="parents" count="2" pageSize="1" target="">'
        '<key name="id" generator="IncrementGenerator"/><condition><if condition="id == 1">'
        '<generate name="children" count="1" target="CSV" exportUri="results">' + a + b + "</generate>"
        '</if><else><generate name="children" count="1" target="CSV" exportUri="results">'
        + (a + b if same_order else b + a)
        + "</generate></else></condition></generate></setup>",
        encoding="utf-8",
    )
    DataMimicTest(tmp_path, "branches.xml").test_with_timer()
    with (tmp_path / "output/results/children.csv").open(newline="") as file:
        assert list(csv.DictReader(file, delimiter="|")) == [{"a": "A", "b": "B"}] * 2
