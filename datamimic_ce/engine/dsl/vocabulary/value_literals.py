# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""CE inline value-list interpretation shared by parsing and execution."""

import ast
from collections.abc import Iterable
from typing import Any


def parse_literal_values(expression: str) -> Any:
    # Keep literal_eval's arbitrary literal types; existing runtime modes interpret them.
    values = ast.literal_eval(expression)
    if not isinstance(values, Iterable) and values is not None:
        return (values,)
    return values
