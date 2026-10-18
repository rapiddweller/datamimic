# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path

import pytest

from datamimic_ce.errors import ErrorCode, InvalidSourceError, IssueCode
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def test_mongodb_missing_selector_and_type():
    engine = DataMimicTest(test_dir=_TEST_DIR, filename="test_mongodb_missing_selector_and_type.xml")
    with pytest.raises(ValueError) as caught:
        engine.test_with_timer()
    assert str(caught.value) == "MongoDB source requires at least attribute 'type', 'selector' or 'iterationSelector'"


@pytest.mark.parametrize(
    "filename,reason",
    [
        (
            "test_mongodb_wrong_query_type.xml",
            "Error while executing query 'update: 'mongo_func_test', filter: {}', "
            "currently Mongodb selector only support 'find' and 'aggregate'",
        ),
        ("test_mongodb_two_find_query.xml", "Error syntax, only 1 'find' allow but found 2"),
        ("test_mongodb_two_aggregate_query.xml", "Error syntax, only 1 'aggregate' allow but found 2"),
        (
            "test_mongodb_find_and_aggregate_error.xml",
            "Error syntax, only one query type allow but found both 'find' and 'aggregate'",
        ),
        ("test_mongodb_two_filter.xml", "Error syntax, only 1 'filter' allow but found 2"),
        ("test_mongodb_two_projection.xml", "Error syntax, only 1 'projection' allow but found 2"),
        ("test_mongodb_two_pipeline.xml", "Error syntax, only 1 'pipeline' allow but found 2"),
        ("test_mongodb_pipeline_syntax_error.xml", "Syntax error: pipeline value must be a list"),
        ("test_mongodb_pipeline_not_exist.xml", "Wrong query syntax 'pipeline' component not found"),
        ("test_mongodb_filter_not_exist.xml", "Wrong query syntax 'filter' component not found"),
    ],
    ids=lambda value: value.removesuffix(".xml") if value.endswith(".xml") else None,
)
def test_mongodb_selector_error_contract(filename, reason):
    engine = DataMimicTest(test_dir=_TEST_DIR, filename=filename)
    with pytest.raises(InvalidSourceError) as caught:
        engine.test_with_timer()
    error = caught.value
    assert isinstance(error, ValueError)
    assert error.error_code is ErrorCode.INVALID_SOURCE
    assert error.issue_code is IssueCode.SOURCE_MONGO_SELECTOR_INVALID
    assert reason in str(error)
    assert str(error).endswith(f"in descriptor '{filename}'")
    assert str(_TEST_DIR) not in str(error)
    assert error.__cause__ is None
