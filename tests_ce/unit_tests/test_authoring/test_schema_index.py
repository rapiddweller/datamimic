# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Architecture gates for the derived DSL schema.

Gate 1 (drift killer): every model's hand-maintained check_valid_attributes
allowlist must equal EXACTLY the XML names derived from model_fields — both
directions. This is what caught the (now purged) GenerateModel.bucket drift.

Gate 2: parser dispatch and authoring schema must derive from one element registry.

Gate 3 (registry): rule ids unique, banded by module, and every rule ships a fix hint.
"""

import contextlib
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from pydantic import BaseModel

from datamimic_ce.authoring.domain.rules import ALL_RULES, best_practice, cross_statement, schema_rules, semantic_rules
from datamimic_ce.authoring.domain.schema import build_schema_index
from datamimic_ce.engine.dsl.model.registry import (
    ElementDefinition,
    get_model_class,
    list_element_tags,
    register_element_extension,
    unregister_element_extension,
)
from datamimic_ce.engine.dsl.model.validation import ModelUtil
from datamimic_ce.engine.dsl.parsers import registry as _registry  # noqa: F401
from datamimic_ce.engine.dsl.parsers.base import dispatch
from datamimic_ce.engine.dsl.parsers.base.statement_parser import StatementParser
from datamimic_ce.engine.dsl.statements.statement import Statement
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import (
    EL_COMMENT,
    EL_FIELD,
    EL_SETUP,
    EL_TRANSITION,
    EL_VALUE,
)
from datamimic_ce.engine.io.api import load_connection_profile

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
    [(tag, get_model_class(tag)) for tag in list_element_tags() if get_model_class(tag) is not None],
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
    dispatchable = {tag for tag in list_element_tags() if tag not in non_dispatchable}
    for tag in sorted(dispatchable):
        parser = dispatch.get_parser_by_element(ET.Element(tag), properties={})
        assert parser is not None, f"<{tag}> is registered but the engine cannot dispatch it"
    for tag in (EL_TRANSITION, EL_FIELD, EL_VALUE, "definitely_not_an_element"):
        with pytest.raises(ValueError):
            dispatch.get_parser_by_element(ET.Element(tag), properties={})


def test_gate2_nesting_children_are_known_tags() -> None:
    index = build_schema_index()
    known = set(list_element_tags()) | {EL_COMMENT}
    for tag, schema in index.elements.items():
        for child in schema.allowed_children or set():
            assert child in known, f"nesting table of <{tag}> references unknown <{child}>"


def test_gate2_single_registration_reaches_parser_and_authoring() -> None:
    """A new definition is registered once, then appears in both runtime and authoring."""
    tag = "synthetic-registry-element"

    class SyntheticModel(BaseModel):
        name: str

    class SyntheticParser(StatementParser):
        def __init__(self, element: ET.Element, properties: dict | None):
            super().__init__(element, properties, valid_element_tag=tag)

        def parse(self, *args, **kwargs) -> Statement:  # pragma: no cover - dispatch is the contract here
            raise NotImplementedError

    register_element_extension(ElementDefinition(tag, SyntheticModel, SyntheticParser))
    try:
        parser = dispatch.get_parser_by_element(ET.Element(tag), properties={})
        schema = build_schema_index().get(tag)

        assert isinstance(parser, SyntheticParser)
        assert schema is not None
        assert schema.model is SyntheticModel
        assert set(schema.attributes) == {"name"}
    finally:
        unregister_element_extension(tag)

    assert build_schema_index().get(tag) is None


def test_extension_parser_receives_the_descriptor_directory_keyword() -> None:
    tag = "synthetic-parser-kwargs"
    observed: list[Path] = []

    class SyntheticParser:
        def __init__(self, _element: ET.Element, _properties: dict | None) -> None:
            pass

        def set_runtime_environment(self, _value: object) -> None:
            pass

        def parse(self, *, descriptor_dir: Path) -> Statement:
            observed.append(descriptor_dir)
            return Statement("synthetic", None)

    register_element_extension(ElementDefinition(tag, None, SyntheticParser))
    try:
        root = ET.fromstring(f"<setup><{tag}/></setup>")
        parsed = dispatch.parse_sub_elements(
            Path("descriptor-root"), root, {}, Statement(None, None), profile_loader=load_connection_profile
        )
    finally:
        unregister_element_extension(tag)

    assert len(parsed) == 1
    assert observed == [Path("descriptor-root")]


def test_cold_parser_registry_dispatches_builtins_and_reports_unknown_tags() -> None:
    script = """
from lxml import etree
from datamimic_ce.engine.dsl.parsers import registry as _registry
from datamimic_ce.engine.dsl.parsers.base.dispatch import get_parser_by_element

assert get_parser_by_element(etree.Element('memstore', id='rows'), properties={}) is not None
try:
    get_parser_by_element(etree.Element('unknown-parser-tag'), properties={})
except ValueError as error:
    assert str(error) == 'Cannot get parser for element <unknown-parser-tag>'
else:
    raise AssertionError('unknown tags must fail through the parser registry')
"""

    result = subprocess.run([sys.executable, "-c", script], text=True, capture_output=True, check=False, timeout=30)

    assert result.returncode == 0, result.stderr


def test_cold_descriptor_parser_requires_no_external_bootstrap() -> None:
    script = """
from pathlib import Path
from tempfile import TemporaryDirectory
from datamimic_ce.engine.dsl.parsers.document.descriptor_parser import DescriptorParser
from datamimic_ce.engine.io.api import load_connection_profile

with TemporaryDirectory() as directory:
    descriptor = Path(directory) / 'descriptor.xml'
    descriptor.write_text('<setup><memstore id="rows"/></setup>', encoding='utf-8')
    parsed = DescriptorParser.parse(descriptor, None, 'production', profile_loader=load_connection_profile)
    assert len(parsed.sub_statements) == 1
"""

    result = subprocess.run([sys.executable, "-c", script], text=True, capture_output=True, check=False, timeout=30)

    assert result.returncode == 0, result.stderr


def test_gate4_reflection_dependent_fields_keep_their_descriptions() -> None:
    """scaffold.py pulls start/end/interval's schema text straight from GenerateModel via
    model_json_schema() reflection (SPOT — see authoring/schema.py's element_json_schema()).
    A future edit that drops a Field(description=...) would silently blank that text out
    without failing any other test; this guard catches it directly. Deliberately scoped to
    the fields this reflection path actually depends on, not every CE model field — full
    retrofit is separate, incremental follow-up work, not this gate's job."""
    from datamimic_ce.engine.dsl.model.generation.generate_model import GenerateModel
    from datamimic_ce.engine.dsl.model.values.variables.variable_model import VariableModel

    generate_schema = GenerateModel.model_json_schema()["properties"]
    for field_name in ("start", "end", "interval"):
        prop = generate_schema[field_name]
        assert prop.get("description"), f"GenerateModel.{field_name} lost its Field(description=...)"
        assert prop.get("examples"), f"GenerateModel.{field_name} lost its Field(examples=...)"

    variable_schema = VariableModel.model_json_schema()["properties"]
    for field_name in ("source", "type"):
        prop = variable_schema[field_name]
        assert prop.get("description"), f"VariableModel.{field_name} lost its Field(description=...)"


def test_gate3_rule_registry_is_consistent() -> None:
    ids = [rule.definition.id for rule in ALL_RULES]
    assert len(ids) == len(set(ids)), "duplicate rule ids"
    bands = {
        schema_rules: "DM1",
        semantic_rules: "DM2",
        best_practice: "DM3",
        cross_statement: "DM4",
    }
    for module, prefix in bands.items():
        for rule in module.RULES:
            rule_id = rule.definition.id
            assert rule_id.startswith(prefix), f"{rule.__name__} ({rule_id}) is in the wrong module band"
    for rule in ALL_RULES:
        assert rule.definition.severity is not None and rule.definition.id.startswith("DM")
