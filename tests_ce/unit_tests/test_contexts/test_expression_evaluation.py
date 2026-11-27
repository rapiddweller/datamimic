# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

from tests_ce.expression_test_context import expression_context


def test_text_from_data_is_not_kept_in_the_compile_cache() -> None:
    """Data text is a value per row; caching it would retain each distinct text."""
    from datamimic_ce.engine.runtime.scripting import evaluation

    context = expression_context()
    big = "'" + "a" * 1_000_000 + "'"
    evaluation._compiled.cache_clear()
    assert len(context.evaluate_python_expression(big, text_from_data=True)) == 1_000_000
    assert evaluation._compiled.cache_info().currsize == 0
    context.evaluate_python_expression("40 + 2")
    assert evaluation._compiled.cache_info().currsize == 1
