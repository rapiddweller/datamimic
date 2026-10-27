# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""CE inline value-list interpretation shared by parsing and execution."""

import ast
import keyword
import re
from collections.abc import Iterable
from typing import Any

# Two or more comma-separated ASCII names: letters, digits and underscore, no digit first, no spaces.
_PLAIN_NAMES = r"[A-Za-z_][A-Za-z0-9_]*(?:,[A-Za-z_][A-Za-z0-9_]*)+"


def parse_literal_values(expression: str) -> Any:
    # Keep literal_eval's arbitrary literal types; existing runtime modes interpret them.
    try:
        values = ast.literal_eval(expression)
    except (ValueError, SyntaxError):
        # A list of plain ASCII names (LOW,MEDIUM,HIGH) can only mean strings; a keyword such as True would be a
        # string here and a bool in True,False, so it keeps the list an error.
        if re.fullmatch(_PLAIN_NAMES, expression) and not any(map(keyword.iskeyword, expression.split(","))):
            return tuple(expression.split(","))
        raise
    if not isinstance(values, Iterable) and values is not None:
        return (values,)
    return values
