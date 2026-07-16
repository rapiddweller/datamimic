# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

"""Authoring rule catalog: severity, definitions, and the canonical DMxxx catalogue.

RuleDefinition IDs, fix-hints, examples, and documentation are authoring/diagnostic
metadata. The runtime engine should not depend on them.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType


class RuleSeverity(StrEnum):
    """Canonical severity vocabulary for public authoring rules."""

    ERROR = "error"
    WARNING = "warning"
    HINT = "hint"


@dataclass(frozen=True)
class RuleDefinition:
    """Immutable public metadata for one authoring evaluator.

    Evaluators only decide whether a definition applies and may add concrete
    runtime details. Identity, severity, canonical explanation, remediation and
    provenance are owned here so CLI, MCP, diagnostics and reference cannot drift.
    """

    id: str
    severity: RuleSeverity
    title: str
    explanation: str
    fix_hint: str
    provenance: str
    valid_example: str
    invalid_example: str
    advisory_severity: RuleSeverity | None = None

    def __post_init__(self) -> None:
        if len(self.id) != 5 or not self.id.startswith("DM") or not self.id[2:].isdigit():
            raise ValueError(f"invalid authoring rule id: {self.id!r}")
        required = (
            self.title,
            self.explanation,
            self.fix_hint,
            self.provenance,
            self.valid_example,
            self.invalid_example,
        )
        if not all(value.strip() for value in required):
            raise ValueError(f"authoring rule {self.id} has empty required metadata")

    @property
    def docs(self) -> str:
        return f"reference://rules/{self.id}"

    def severity_for(self, *, advisory: bool = False) -> RuleSeverity:
        if advisory and self.advisory_severity is not None:
            return self.advisory_severity
        return self.severity


def _rule_definition(
    rule_id: str,
    severity: RuleSeverity,
    title: str,
    explanation: str,
    fix_hint: str,
    provenance: str,
    valid_example: str,
    invalid_example: str,
    advisory_severity: RuleSeverity | None = None,
) -> RuleDefinition:
    return RuleDefinition(
        id=rule_id,
        severity=severity,
        title=title,
        explanation=explanation,
        fix_hint=fix_hint,
        provenance=provenance,
        valid_example=valid_example,
        invalid_example=invalid_example,
        advisory_severity=advisory_severity,
    )


# Public authoring evaluator catalog. Keep IDs stable: benchmark fixtures and
# downstream agent tooling use them as machine contracts.
_MINIMAL_GENERATE_EXAMPLE = '<generate name="g" count="1"/>'

_AUTHORING_RULE_DEFINITIONS: tuple[RuleDefinition, ...] = (
    _rule_definition(
        "DM101",
        RuleSeverity.ERROR,
        "Unknown element",
        "The descriptor uses an element outside the live CE registry.",
        "Use a registered element name.",
        "Element registry and parser dispatch contract.",
        '<setup><generate name="g" count="1"/></setup>',
        '<setup><generat name="g"/></setup>',
    ),
    _rule_definition(
        "DM102",
        RuleSeverity.ERROR,
        "Invalid child element",
        "A registered element appears under a parent that does not allow it.",
        "Move the child to an allowed parent.",
        "Element registry nesting contract.",
        '<setup><generate name="g" count="1"/></setup>',
        '<setup><key name="x" constant="1"/></setup>',
    ),
    _rule_definition(
        "DM103",
        RuleSeverity.ERROR,
        "Unknown attribute",
        "An element contains an attribute absent from its registered runtime model.",
        "Use an attribute exposed by the element model.",
        "Pydantic runtime model field contract.",
        _MINIMAL_GENERATE_EXAMPLE,
        '<generate name="g" couunt="1"/>',
    ),
    _rule_definition(
        "DM104",
        RuleSeverity.ERROR,
        "Missing required attribute",
        "A required runtime-model attribute is absent.",
        "Add the required attribute.",
        "Pydantic runtime model required-field contract.",
        _MINIMAL_GENERATE_EXAMPLE,
        '<generate count="1"/>',
    ),
    _rule_definition(
        "DM105",
        RuleSeverity.ERROR,
        "Invalid attribute value",
        "An attribute value is outside the vocabulary derived for its element context.",
        "Choose a value exposed by the element model and central constraint facts.",
        "Runtime enums and model constraint registry.",
        '<key name="x" type="int"/>',
        '<key name="x" type="integer"/>',
    ),
    _rule_definition(
        "DM106",
        RuleSeverity.ERROR,
        "Invalid root element",
        "Every DATAMIMIC descriptor must have setup as its root.",
        "Wrap the descriptor in a setup element.",
        "Setup parser root contract.",
        "<setup/>",
        _MINIMAL_GENERATE_EXAMPLE,
    ),
    _rule_definition(
        "DM107",
        RuleSeverity.ERROR,
        "Leaf has children",
        "A leaf element contains child elements.",
        "Remove the child or move it to a container.",
        "Element registry nesting contract.",
        '<key name="x" constant="1"/>',
        '<key name="x" constant="1"><value>1</value></key>',
    ),
    _rule_definition(
        "DM201",
        RuleSeverity.ERROR,
        "Conflicting count bounds",
        "count cannot be combined with minCount or maxCount, and bounds must be ordered.",
        "Use count or a minCount/maxCount range.",
        "ModelUtil count-bound validation.",
        '<generate name="g" minCount="1" maxCount="2"/>',
        '<generate name="g" count="1" minCount="1"/>',
    ),
    _rule_definition(
        "DM202",
        RuleSeverity.ERROR,
        "Missing row cardinality",
        "A generate-like statement needs count, a count range, source or script unless "
        "another declared mode supplies cardinality.",
        "Add a supported cardinality source.",
        "EXIST_COUNT central constraint and ADR-006 count fallback.",
        _MINIMAL_GENERATE_EXAMPLE,
        '<generate name="g"/>',
    ),
    _rule_definition(
        "DM203",
        RuleSeverity.ERROR,
        "Conflicting generation modes",
        "A field must select exactly one declared value-source mode; weights additionally require values.",
        "Keep one value source and its required companions.",
        "Central generation-mode constraints.",
        '<key name="x" constant="1"/>',
        '<key name="x" constant="1" script="2"/>',
        RuleSeverity.WARNING,
    ),
    _rule_definition(
        "DM204",
        RuleSeverity.ERROR,
        "Invalid unique combination",
        "unique requires a finite pool and must follow the element's central distribution policy.",
        "Use a supported finite pool and remove conflicting weights, cyclic or distribution attributes.",
        "Central unique/source compatibility facts and ADR-042.",
        '<variable name="x" values="1,2" unique="true"/>',
        '<variable name="x" values="1,2" unique="true" cyclic="true"/>',
    ),
    _rule_definition(
        "DM205",
        RuleSeverity.ERROR,
        "Conflicting source mode",
        "A gated source mode combines mutually exclusive attributes.",
        "Keep only one source selector/type mode.",
        "MutuallyExclusiveWhen central constraint.",
        '<variable name="x" source="rows.csv" type="row"/>',
        '<variable name="x" source="rows.csv" type="row" selector="all"/>',
        RuleSeverity.WARNING,
    ),
    _rule_definition(
        "DM211",
        RuleSeverity.ERROR,
        "Selector lacks resolvable count",
        "selector without a count is only cardinality-safe for a declared database client.",
        "Add count bounds or use a declared database/mongodb source.",
        "GenerateTask and VariableTask database selector contract.",
        '<generate name="g" source="db" selector="select *"/>',
        '<generate name="g" source="rows.csv" selector="all"/>',
    ),
    _rule_definition(
        "DM212",
        RuleSeverity.ERROR,
        "Invalid count expression",
        "count must be an integer literal or a supported script expression.",
        "Use digits or a {script} expression.",
        "ModelUtil count parser contract.",
        '<generate name="g" count="3"/>',
        '<generate name="g" count="three"/>',
    ),
    _rule_definition(
        "DM213",
        RuleSeverity.ERROR,
        "Unbounded nested cycle",
        "A cyclic nestedKey without count bounds cannot terminate.",
        "Add count, minCount or maxCount.",
        "NestedKey runtime length contract.",
        '<nestedKey name="x" source="rows.csv" cyclic="true" count="2"/>',
        '<nestedKey name="x" source="rows.csv" cyclic="true"/>',
    ),
    _rule_definition(
        "DM214",
        RuleSeverity.ERROR,
        "Missing companion attribute",
        "A declared companion attribute is present without the mode it requires.",
        "Add the required mode attribute or remove the companion.",
        "Central Requires constraints.",
        '<variable name="x" source="rows.csv" separator=","/>',
        '<variable name="x" separator=","/>',
        RuleSeverity.WARNING,
    ),
    _rule_definition(
        "DM216",
        RuleSeverity.WARNING,
        "Nested key has no data mode",
        "A nestedKey with children but no type, source or script expects a pre-existing field.",
        "Select list/dict, source or script unless template enrichment is intentional.",
        "NestedKey template-enrichment runtime branch.",
        '<nestedKey name="x" type="dict"><key name="a" constant="1"/></nestedKey>',
        '<nestedKey name="x"><key name="a" constant="1"/></nestedKey>',
    ),
    _rule_definition(
        "DM217",
        RuleSeverity.ERROR,
        "Incomplete attribute group",
        "An all-or-none attribute group is only partially configured.",
        "Provide the complete group or remove it.",
        "Central AllOrNone constraints.",
        '<generate name="g" start="2025-01-01" end="2025-01-02" interval="P1D"/>',
        '<generate name="g" start="2025-01-01"/>',
        RuleSeverity.WARNING,
    ),
    _rule_definition(
        "DM218",
        RuleSeverity.ERROR,
        "Forbidden attribute combination",
        "A central Forbids constraint is violated.",
        "Remove the forbidden companion or the gating attribute.",
        "Central Forbids constraints.",
        '<nestedKey name="x" script="{}"/>',
        '<nestedKey name="x" script="{}" type="dict"/>',
        RuleSeverity.WARNING,
    ),
    _rule_definition(
        "DM219",
        RuleSeverity.ERROR,
        "Invalid declared value",
        "A non-type attribute is outside its centrally declared valid values.",
        "Use one of the values exposed by the central constraint.",
        "Central ValidValues constraints.",
        '<variable name="x" constant="1" storage="value"/>',
        '<variable name="x" constant="1" storage="unknown"/>',
        RuleSeverity.WARNING,
    ),
    _rule_definition(
        "DM220",
        RuleSeverity.ERROR,
        "Invalid gated value",
        "An attribute value violates a centrally declared gated allowed-values rule.",
        "Use an allowed value for the active mode.",
        "Central AllowedValuesWhen constraints.",
        '<key name="x" type="string" outDateFormat="%Y"/>',
        '<key name="x" type="int" outDateFormat="%Y"/>',
        RuleSeverity.WARNING,
    ),
    _rule_definition(
        "DM221",
        RuleSeverity.ERROR,
        "Invalid conditional attributes",
        "A value-gated central constraint is violated.",
        "Use only attributes permitted by the selected mode.",
        "Central RequiresWhenValue and ForbidsWhenValue constraints.",
        '<array name="x" type="string" count="1"/>',
        '<array name="x" type="literal" count="1"/>',
        RuleSeverity.WARNING,
    ),
    _rule_definition(
        "DM301",
        RuleSeverity.WARNING,
        "Implicit random source order",
        "A source read without distribution uses random order, not source order.",
        "Set distribution explicitly to ordered or random.",
        "SourceDistribution default runtime contract.",
        '<variable name="x" source="rows.csv" distribution="ordered"/>',
        '<variable name="x" source="rows.csv"/>',
    ),
    _rule_definition(
        "DM302",
        RuleSeverity.HINT,
        "Source is fully materialized",
        "Non-ordered or unique source selection loads the complete source into memory.",
        "Use ordered for bounded paging or accept the memory cost explicitly.",
        "SourceDistribution.loads_all runtime contract.",
        '<variable name="x" source="rows.csv" distribution="ordered"/>',
        '<variable name="x" source="rows.csv" distribution="random"/>',
    ),
    _rule_definition(
        "DM303",
        RuleSeverity.HINT,
        "Unseeded run",
        "Without setup rngSeed, repeated executions intentionally differ.",
        "Add rngSeed when deterministic replay is required.",
        "Setup RNG lifecycle contract.",
        '<setup rngSeed="1"/>',
        "<setup/>",
    ),
    _rule_definition(
        "DM304",
        RuleSeverity.HINT,
        "Seed disables multiprocessing",
        "Seeded CE execution is serialized for deterministic replay.",
        "Remove multiprocessing settings or remove rngSeed according to the desired trade-off.",
        "Seeded GenerateTask execution contract.",
        '<setup rngSeed="1"><generate name="g" count="1"/></setup>',
        '<setup rngSeed="1"><generate name="g" count="1" numProcess="2"/></setup>',
    ),
    _rule_definition(
        "DM305",
        RuleSeverity.HINT,
        "Small page size",
        "A pageSize below 100 creates avoidable per-page overhead.",
        "Use pageSize at least 100 or omit it.",
        "Exporter and source paging behavior.",
        '<generate name="g" count="100" pageSize="100"/>',
        '<generate name="g" count="100" pageSize="10"/>',
    ),
    _rule_definition(
        "DM307",
        RuleSeverity.HINT,
        "Zero-count upsert",
        "A mongodb upsert target coerces count zero to one operation.",
        "Expect one upsert or remove the upsert target.",
        "MongoDB upsert runtime contract.",
        '<generate name="g" count="1" target="db.upsert"/>',
        '<generate name="g" count="0" target="db.upsert"/>',
    ),
    _rule_definition(
        "DM310",
        RuleSeverity.HINT,
        "Prefer native numeric range",
        "An eval-string IntegerGenerator duplicates the typed numeric range surface.",
        "Use type, min and max attributes.",
        "Native key range authoring contract.",
        '<key name="x" type="int" min="1" max="9"/>',
        '<key name="x" generator="IntegerGenerator(min=1,max=9)"/>',
    ),
    _rule_definition(
        "DM311",
        RuleSeverity.HINT,
        "Prefer native string bounds",
        "An eval-string StringGenerator duplicates native string length attributes.",
        "Use type=string with minLength/maxLength.",
        "Native key string-bound authoring contract.",
        '<key name="x" type="string" minLength="1" maxLength="9"/>',
        '<key name="x" generator="StringGenerator(min_len=1,max_len=9)"/>',
    ),
    _rule_definition(
        "DM314",
        RuleSeverity.ERROR,
        "Interpolation token in Python",
        "Double-underscore interpolation tokens are invalid inside Python expressions.",
        "Use the bare Python variable name in script or condition.",
        "Expression evaluator and string interpolation contracts.",
        '<key name="x" script="row.value"/>',
        '<key name="x" script="__row__.value"/>',
    ),
    _rule_definition(
        "DM315",
        RuleSeverity.HINT,
        "Nested increment is local",
        "IncrementGenerator restarts per parent inside a nested generate and is a valid local sequence.",
        "Only when global uniqueness is required, compose the parent key with the local sequence.",
        "Generator lifecycle contract and nested-generate regression tests.",
        '<generate name="children" count="2"><key name="line_no" generator="IncrementGenerator"/>'
        '<key name="global_id" script="parent.id * 100 + this.line_no"/></generate>',
        '<generate name="children" count="2"><key name="global_id" generator="IncrementGenerator"/></generate>',
    ),
    _rule_definition(
        "DM316",
        RuleSeverity.HINT,
        "Source count may cap",
        "A non-cyclic source read can stop below count when its source is exhausted.",
        "Enable cyclic wrapping or omit count to consume the source once.",
        "GenerateWorker StopIteration contract.",
        '<iterate name="x" source="rows.csv" distribution="ordered"/>',
        '<iterate name="x" source="rows.csv" count="99" distribution="ordered"/>',
    ),
    _rule_definition(
        "DM317",
        RuleSeverity.ERROR,
        "Nested numeric sequence will exhaust",
        "A finite positional numeric sequence has fewer values than the statically proven nested-scope demand.",
        "Increase the numeric range, reduce the nested cardinality, or use a non-finite per-row distribution.",
        "POSITIONAL_NUMBER_SEQUENCES and number_sequences StopIteration contract.",
        '<key name="n" type="int" min="1" max="16" distribution="step"/>',
        '<key name="n" type="int" min="1" max="2" distribution="step"/>',
    ),
    _rule_definition(
        "DM318",
        RuleSeverity.HINT,
        "Nested numeric sequence capacity is unproven",
        "A finite positional numeric sequence is in a dynamic nested scope, so exhaustion cannot be proven statically.",
        "Make parent and nested counts literal, or size the range for the maximum possible demand.",
        "POSITIONAL_NUMBER_SEQUENCES and dynamic generate cardinality contract.",
        '<generate name="p" count="2"><generate name="c" count="2">'
        '<key name="n" type="int" min="1" max="4" distribution="step"/></generate></generate>',
        '<generate name="p" source="rows.csv"><generate name="c" count="2">'
        '<key name="n" type="int" min="1" max="2" distribution="step"/></generate></generate>',
    ),
    _rule_definition(
        "DM401",
        RuleSeverity.ERROR,
        "Unknown target",
        "A target cannot be parsed or does not resolve to a built-in or declared client/memstore.",
        "Use a built-in target or declare the referenced id and operation.",
        "ExporterUtil target parser and ExportOperation enum.",
        '<generate name="g" count="1" target="JSON"/>',
        '<generate name="g" count="1" target="missing"/>',
    ),
    _rule_definition(
        "DM402",
        RuleSeverity.ERROR,
        "Unknown source",
        "A source is neither a supported data file nor a declared source id.",
        "Use a supported file or declare the memstore/database/mongodb id.",
        "TaskUtil source dispatch contract.",
        '<variable name="x" source="rows.csv"/>',
        '<variable name="x" source="missing"/>',
    ),
    _rule_definition(
        "DM403",
        RuleSeverity.WARNING,
        "Duplicate product name",
        "Sibling generate statements with the same name overwrite or merge captures.",
        "Give sibling products unique names.",
        "Product capture and exporter naming contract.",
        '<setup><generate name="a" count="1"/><generate name="b" count="1"/></setup>',
        '<setup><generate name="a" count="1"/><generate name="a" count="1"/></setup>',
    ),
    _rule_definition(
        "DM404",
        RuleSeverity.WARNING,
        "Nested foreign key does not copy its parent",
        "A nested child foreign-key field is generated independently instead of carrying its enclosing parent key.",
        'Use a nested <key> with script="parent.<field>" to copy the enclosing parent key.',
        "AuthoringSpecV1 nested relationship and foreign-key role contract.",
        '<setup><generate name="customers" count="4"><key name="id" generator="IncrementGenerator"/>'
        '<generate name="orders" count="2"><key name="customer_id" script="parent.id"/>'
        "</generate></generate></setup>",
        '<setup><generate name="customers" count="4"><key name="id" generator="IncrementGenerator"/>'
        '<generate name="orders" count="2"><key name="customer_id" type="int" min="1" max="4"/>'
        "</generate></generate></setup>",
    ),
    _rule_definition(
        "DM405",
        RuleSeverity.ERROR,
        "Missing include file",
        "A statically resolvable include path does not exist beside the descriptor.",
        "Fix the relative path or create the include file.",
        "Include parser path-resolution contract.",
        '<include uri="existing.properties"/>',
        '<include uri="missing.properties"/>',
    ),
    _rule_definition(
        "DM406",
        RuleSeverity.WARNING,
        "Memstore readback field does not copy its source",
        "A same-named field in a memstore-backed source product regenerates a stored value instead of reading it.",
        'Use a script field with script="this.<field>"; retain any foreign-key role on that field.',
        "AuthoringSpecV1 memstore source readback contract.",
        '<setup><memstore id="store"/><generate name="users" count="1" target="store">'
        '<key name="id" generator="IncrementGenerator"/></generate>'
        '<generate name="audit" source="store" type="users"><key name="id" script="this.id"/>'
        "</generate></setup>",
        '<setup><memstore id="store"/><generate name="users" count="1" target="store">'
        '<key name="id" generator="IncrementGenerator"/></generate>'
        '<generate name="audit" source="store" type="users"><key name="id" type="int" min="1" max="9"/>'
        "</generate></setup>",
    ),
)

_AUTHORING_RULE_DEFINITIONS_BY_ID = {definition.id: definition for definition in _AUTHORING_RULE_DEFINITIONS}
if len(_AUTHORING_RULE_DEFINITIONS_BY_ID) != len(_AUTHORING_RULE_DEFINITIONS):
    raise ValueError("duplicate authoring rule ids in central catalog")
AUTHORING_RULE_DEFINITIONS: Mapping[str, RuleDefinition] = MappingProxyType(_AUTHORING_RULE_DEFINITIONS_BY_ID)


def authoring_rule_definitions() -> tuple[RuleDefinition, ...]:
    """All public authoring rules in stable ID order."""
    return tuple(sorted(AUTHORING_RULE_DEFINITIONS.values(), key=lambda definition: definition.id))


def authoring_rule_definition(rule_id: str) -> RuleDefinition:
    """Resolve one public authoring rule by stable ID."""
    return AUTHORING_RULE_DEFINITIONS[rule_id]


def serialize_rule_definition(definition: RuleDefinition) -> dict[str, str]:
    """Project one catalog entry to CLI/MCP-friendly plain data."""
    serialized = {
        "id": definition.id,
        "severity": definition.severity.value,
        "title": definition.title,
        "explanation": definition.explanation,
        "fix_hint": definition.fix_hint,
        "provenance": definition.provenance,
        "valid_example": definition.valid_example,
        "invalid_example": definition.invalid_example,
        "docs": definition.docs,
    }
    if definition.advisory_severity is not None:
        serialized["advisory_severity"] = definition.advisory_severity.value
    return serialized
