# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""The GBNF grammar must stay derived from the engine registries (SPOT) and be
well-formed (every referenced rule defined) so it is safe to feed to a decoder."""

import re

import pytest

from datamimic_ce.authoring.gbnf import descriptor_grammar
from datamimic_ce.constants.data_type_constants import DATA_TYPE_DECIMAL, DATA_TYPE_INT, DATA_TYPE_STRING
from datamimic_ce.exporters.exporter_util import _BUFFERED_EXPORTERS


def _rules(grammar: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in re.finditer(r"^([\w-]+)\s*::=(.*)$", grammar, re.MULTILINE)}


def test_grammar_is_well_formed() -> None:
    grammar = descriptor_grammar()
    rules = _rules(grammar)
    assert "root" in rules
    # every referenced non-terminal must be defined (catch typos before a decoder chokes)
    referenced = set()
    for body in rules.values():
        # strip string literals and [char-classes]; what remains are rule references
        bare = re.sub(r'"(\\.|[^"\\])*"', " ", body)
        bare = re.sub(r"\[[^\]]*\]", " ", bare)
        referenced.update(re.findall(r"\b([a-z][\w-]+)\b", bare))
    dangling = referenced - set(rules)
    assert not dangling, f"grammar references undefined rules: {dangling}"


def test_targets_and_types_derived_from_registries() -> None:
    grammar = descriptor_grammar()
    # SPOT: every real file exporter appears as a target literal (GBNF-escaped); nothing invented
    for target in _BUFFERED_EXPORTERS:
        assert f'\\"{target}\\"' in grammar, f"target {target} missing from grammar"
    for dtype in (DATA_TYPE_INT, DATA_TYPE_DECIMAL, DATA_TYPE_STRING):
        assert f'type=\\"{dtype}\\"' in grammar


def test_grammar_encodes_domain_and_single_value_source() -> None:
    grammar = descriptor_grammar()
    # domain branches (real person data) + the exactly-one-value-source alternation (no DM203)
    assert 'script=\\"person.name\\"' in grammar and 'script=\\"person.email\\"' in grammar
    assert "value-source ::=" in grammar and "|" in _rules(grammar)["value-source"]


def test_grammar_compiles_in_llama_cpp() -> None:
    # Optional: only when llama-cpp-python is installed (not a base dependency).
    grammar_mod = pytest.importorskip("llama_cpp", reason="llama-cpp-python not installed")
    grammar_mod.LlamaGrammar.from_string(descriptor_grammar())  # raises on a malformed grammar
