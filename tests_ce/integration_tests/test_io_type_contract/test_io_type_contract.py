# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import pytest

from datamimic_ce.errors import TaskConfigError
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


def test_memstore_reads_after_filtering_against_sqlite(project_dir):
    engine = DataMimicTest(test_dir=project_dir, filename="datamimic.xml", capture_test_result=True)
    engine.test_with_timer()

    result = engine.capture_result()
    assert result["full"] == [{"ids": "1,3"}]
    assert [(row["id"], row["label"]) for row in result["paged"]] == [("1", "edited in store"), ("3", "unchanged")]


def test_memstore_filter_without_client_method_keeps_native_failure(project_dir):
    descriptor = project_dir / "datamimic.xml"
    script = descriptor.read_text(encoding="utf-8")
    target = '"reference_ids", db)'
    assert script.count(target) == 1
    descriptor.write_text(script.replace(target, '"reference_ids", object())'), encoding="utf-8")
    engine = DataMimicTest(test_dir=project_dir, filename=descriptor.name, capture_test_result=True)

    with pytest.raises(TaskConfigError) as failure:
        engine.test_with_timer()

    assert isinstance(failure.value.__cause__, AttributeError)
    assert "get_random_rows_by_columns" in str(failure.value.__cause__)
