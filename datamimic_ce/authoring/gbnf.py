# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

# ruff: noqa: E501 — GBNF rules are one-per-line and intrinsically long.

"""A GBNF grammar that constrains an LLM to generate structurally-valid DATAMIMIC
descriptors.

For constrained decoding (llama.cpp ``--grammar-file`` / the ``grammar=`` API,
or any runtime that consumes GBNF). Token-level masking makes malformed XML,
unknown elements, unknown attributes, missing required attributes and multi-mode
keys STRUCTURALLY IMPOSSIBLE — the model only chooses names, counts, and one
value source per key. Structural validity is the grammar's job; value semantics
(min<max, does the country come from the right list) still need a repair pass or
the lint/dry-run loop, and — for a small model — the intent->construct mapping in
the reference cheatsheet belongs in the *prompt* (grammar rule names are invisible
to the model; see reference.py).

Targets and data types are derived from the engine registries so the grammar
cannot drift from the DSL (SPOT).
"""

from datamimic_ce.constants.data_type_constants import (
    DATA_TYPE_DECIMAL,
    DATA_TYPE_FLOAT,
    DATA_TYPE_INT,
    DATA_TYPE_STRING,
)
from datamimic_ce.exporters.exporter_util import _BUFFERED_EXPORTERS


def _alt(literals: list[str]) -> str:
    """GBNF alternation of quoted string literals, e.g. '"JSON" | "CSV"'."""
    return " | ".join(f'"\\"{lit}\\""' for lit in literals)


def descriptor_grammar() -> str:
    """Return a GBNF grammar for structurally-valid DATAMIMIC descriptors."""
    file_targets = sorted(_BUFFERED_EXPORTERS)  # CSV/JSON/XML/XLSX/TXT/DbUnit — real file exporters
    return _GRAMMAR_TEMPLATE.format(
        targets=_alt(file_targets),
        int_type=DATA_TYPE_INT,
        decimal_type=DATA_TYPE_DECIMAL,
        float_type=DATA_TYPE_FLOAT,
        string_type=DATA_TYPE_STRING,
    )


# A <key>'s value source is a single alternation -> exactly-one-mode is guaranteed (no DM203).
# person-name/email reference the mandatory <variable entity="Person"> -> real domain data.
_GRAMMAR_TEMPLATE = r'''root ::= "<setup rngSeed=\"1\">\n" gen-block gen-block? gen-block? "</setup>"
gen-block ::= "  <generate name=" ident " count=" small-int " target=" export-target ">\n" "    <variable name=\"person\" entity=\"Person\"/>\n" field field? field? field? field? field? "  </generate>\n"
field ::= data-field | nested-field
data-field ::= "    <key name=" ident " " value-source "/>\n"
value-source ::= incr-id | int-range | dec-range | str-len | pick-list | weighted-list | regex-pat | person-name | person-email | const-val | script-expr
incr-id ::= "generator=\"IncrementGenerator\""
int-range ::= "type=\"{int_type}\" min=" small-int " max=" big-int
dec-range ::= "type=\"{decimal_type}\" min=" small-int " max=" big-int
str-len ::= "type=\"{string_type}\" minLength=" small-int " maxLength=" small-int
pick-list ::= "values=" value-list
weighted-list ::= "values=" value-list " weights=" weight-list
regex-pat ::= "pattern=" quoted-pat
person-name ::= "script=\"person.name\""
person-email ::= "script=\"person.email\""
const-val ::= "constant=" quoted-word
script-expr ::= "script=" quoted-word
nested-field ::= "    <nestedKey name=" ident " type=\"list\" minCount=" small-int " maxCount=" small-int ">\n" nkey nkey? nkey? "    </nestedKey>\n"
nkey ::= "      <key name=" ident " " leaf-source "/>\n"
leaf-source ::= incr-id | int-range | pick-list | regex-pat | const-val
export-target ::= {targets}
ident ::= "\"" [a-z] [a-z0-9_]{{1,14}} "\""
quoted-word ::= "\"" [a-zA-Z0-9 _.-]{{1,20}} "\""
small-int ::= "\"" [1-9] [0-9]{{0,1}} "\""
big-int ::= "\"" [1-9] [0-9]{{0,5}} "\""
value-list ::= "\"'" word "'" ("," "'" word "'"){{1,5}} "\""
weight-list ::= "\"0." digit ("," "0." digit){{1,5}} "\""
quoted-pat ::= "\"" pat-char{{3,14}} "\""
pat-char ::= [A-Za-z0-9] | "[" | "]" | "{{" | "}}" | "-"
word ::= [A-Za-z] [A-Za-z0-9 ]{{0,10}}
digit ::= [0-9]
'''
