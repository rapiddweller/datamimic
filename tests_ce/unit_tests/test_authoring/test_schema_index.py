# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Architecture gates for the derived DSL schema.

Gate 1 (drift killer): every model's hand-maintained check_valid_attributes
allowlist must equal EXACTLY the XML names derived from model_fields — both
directions. This is what caught the (now purged) GenerateModel.bucket drift.

Gate 2: the linter's ELEMENT_MODEL_MAP must match the engine's parser dispatch.

Gate 3 (registry): rule ids unique, banded by module, and every rule ships a fix hint.
"""

import contextlib
import xml.etree.ElementTree as ET

import pytest
from pydantic import BaseModel

from datamimic_ce.authoring.rules import ALL_RULES, best_practice, cross_statement, schema_rules, semantic_rules
from datamimic_ce.authoring.schema import ELEMENT_MODEL_MAP, build_schema_index
from datamimic_ce.constants.element_constants import EL_COMMENT, EL_FIELD, EL_SETUP, EL_TRANSITION, EL_VALUE
from datamimic_ce.model.model_util import ModelUtil
from datamimic_ce.parsers.parser_util import ParserUtil

# Models that intentionally have no check_valid_attributes guard:
# database/mongodb take open credential attributes (extra="allow").
_UNGUARDED_OK = {"DatabaseModel", "MongoDBModel"}


def _derived_xml_names(model: type[BaseModel]) -> set[str]:
    return {field.alias or name for name, field in model.model_fields.items()}


# Minimal attrs that satisfy the models' OTHER before-validators so the allowlist
# guard actually runs (pydantic executes before-validators in reverse definition
# order — a failing sibling validator would mask the guard for the probe).
_PROBE_ATTEMPTS: tuple[dict[str, str], ...] = (
    {},
    {"name": "x"},
    {"name": "x", "count": "1"},
    {"name": "x", "constant": "1"},
    {"name": "x", "count": "3", "type": "string"},
    {"name": "x", "uri": "u"},
    {"name": "x", "script": "1"},
)


@pytest.mark.parametrize(
    "tag,model",
    [(tag, model) for tag, model in sorted(ELEMENT_MODEL_MAP.items()) if model is not None],
    ids=lambda value: value if isinstance(value, str) else value.__name__,
)
def test_gate1_allowlist_matches_model_fields(tag: str, model: type[BaseModel], monkeypatch) -> None:
    recorded: list[set[str]] = []
    original = ModelUtil.check_valid_attributes

    def spy(values: dict, valid_attributes: set) -> dict:
        recorded.append(set(valid_attributes))
        return original(values=values, valid_attributes=valid_attributes)

    monkeypatch.setattr(ModelUtil, "check_valid_attributes", spy)
    for attempt in _PROBE_ATTEMPTS:
        with contextlib.suppress(Exception):  # validation may fail around the guard — we only need the recording
            model.model_validate(attempt)
        if recorded:
            break

    if not recorded:
        assert model.__name__ in _UNGUARDED_OK, (
            f"<{tag}> ({model.__name__}) has no check_valid_attributes guard — "
            "unknown attributes are silently ignored; add the guard or whitelist here"
        )
        return

    allowlist = recorded[0]
    derived = _derived_xml_names(model)
    assert allowlist == derived, (
        f"<{tag}> ({model.__name__}) allowlist drifted from model_fields: "
        f"missing from allowlist: {sorted(derived - allowlist)}; "
        f"not a field: {sorted(allowlist - derived)}"
    )


def test_gate2_dispatch_accepts_exactly_the_mapped_tags() -> None:
    # <setup> is the root (parsed by SetupParser directly); <transition> is parsed
    # inside <state-machine>, <field> inside <reference>, <value> inside a literal
    # <array> — none is dispatched standalone.
    non_dispatchable = (EL_SETUP, EL_COMMENT, EL_TRANSITION, EL_FIELD, EL_VALUE)
    dispatchable = {tag for tag in ELEMENT_MODEL_MAP if tag not in non_dispatchable}
    for tag in sorted(dispatchable):
        parser = ParserUtil._get_parser_by_element(ET.Element(tag), properties=None)
        assert parser is not None, f"<{tag}> is in ELEMENT_MODEL_MAP but the engine cannot dispatch it"
    for tag in (EL_TRANSITION, EL_FIELD, EL_VALUE, "definitely_not_an_element"):
        with pytest.raises(ValueError):
            ParserUtil._get_parser_by_element(ET.Element(tag), properties=None)


def test_gate2_nesting_children_are_known_tags() -> None:
    index = build_schema_index()
    known = set(ELEMENT_MODEL_MAP) | {EL_COMMENT}
    for tag, schema in index.elements.items():
        for child in schema.allowed_children or set():
            assert child in known, f"nesting table of <{tag}> references unknown <{child}>"


def test_gate3_rule_registry_is_consistent() -> None:
    ids = [rule.id for rule in ALL_RULES]
    assert len(ids) == len(set(ids)), "duplicate rule ids"
    bands = {
        schema_rules: "DM1",
        semantic_rules: "DM2",
        best_practice: "DM3",
        cross_statement: "DM4",
    }
    for module, prefix in bands.items():
        for rule in module.RULES:
            assert rule.id.startswith(prefix), f"{rule.__name__} ({rule.id}) is in the wrong module band"
    for rule in ALL_RULES:
        assert rule.severity is not None and rule.id.startswith("DM")
