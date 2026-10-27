# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""values= reads Python literals; a list of plain names is read as strings (5 of 50 blind first Builds at
89f304b9 wrote values="LOW,MEDIUM,HIGH"). Every other unquoted form stays an error. One parser serves Build and
datamimic run; tests_ce/scenarios/s25_bare_value_list runs both."""

import pytest

from datamimic_ce.engine.dsl.vocabulary.value_literals import parse_literal_values


@pytest.mark.parametrize(
    ("expression", "values"),
    [
        ("LOW,MEDIUM,HIGH", ("LOW", "MEDIUM", "HIGH")),
        ("basic_1,PLUS_2", ("basic_1", "PLUS_2")),
        ("_a,b", ("_a", "b")),
        ("'LOW','HIGH'", ("LOW", "HIGH")),
        ("1,2,3", (1, 2, 3)),
        ("True,False", (True, False)),
        ("[1, 2]", [1, 2]),
    ],
)
def test_literals_and_lists_of_plain_names_are_read(expression: str, values: object) -> None:
    assert parse_literal_values(expression) == values


@pytest.mark.parametrize(
    "expression",
    [
        "LOW",  # one name: a typo of a quoted literal as likely as a list
        "LOW, MEDIUM",  # space
        "LOW,True",  # a keyword would be a string here and a bool in True,False
        "LOW,None",
        "LOW,1A",  # a token that starts with a digit
        "LOW,",  # empty token
        ",LOW",
        "LOW,'HIGH'",  # mixed quoting
        "LOW,f(x)",
        "LOW,MÉDIUM",  # not ASCII
        "",
    ],
)
def test_every_other_unquoted_form_stays_an_error(expression: str) -> None:
    with pytest.raises((ValueError, SyntaxError)):
        parse_literal_values(expression)


def test_plain_names_are_strings_even_when_a_variable_has_the_same_name() -> None:
    # The names are never variable references: a name that matches a variable still reads as text.
    assert parse_literal_values("LOW,HIGH") == ("LOW", "HIGH")
