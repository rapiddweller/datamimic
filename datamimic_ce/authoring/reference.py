# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""DSL reference for agents: element schemas, generators, targets, distributions —
everything derived from the engine's registries or gate-tested content.
Token-capped: every answer ends with a pointer instead of overflowing."""

import importlib
import inspect
import json
import pkgutil
from functools import lru_cache
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datamimic_ce.domains.domain_core.entity_registry import EntitySpec

from datamimic_ce.authoring.contracts import ReferenceTopic
from datamimic_ce.authoring.reference_projection import (
    AuthoringReferenceQuery,
    authoring_reference_projection,
    list_authoring_reference_queries,
)
from datamimic_ce.authoring.rule_catalog import (
    authoring_rule_definition,
    authoring_rule_definitions,
    serialize_rule_definition,
)
from datamimic_ce.authoring.schema import ElementSchema, build_schema_index
from datamimic_ce.constants.exporter_constants import (
    EXPORTER_CONSOLE_EXPORTER,
    EXPORTER_LOG_EXPORTER,
    EXPORTER_TEST_RESULT_EXPORTER,
)
from datamimic_ce.model.constraints import (
    KEY_DISTRIBUTION_VALUES,
    SOURCE_DISTRIBUTION_VALUES,
    AllOrNone,
    AllowedValuesWhen,
    Forbids,
    ForbidsWhenValue,
    MutuallyExclusive,
    MutuallyExclusiveWhen,
    RequiredOneOf,
    Requires,
    RequiresWhenValue,
    ValidValues,
    resolved_values,
    serialize_constraints,
    serialize_source_capability,
    source_capabilities,
)
from datamimic_ce.model.element_registry import canonical_tag, element_aliases

_GENERATOR_PACKAGE = "datamimic_ce.domains.common.literal_generators"


def clip(text: str, max_chars: int, hint: str) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - len(hint) - 2].rstrip() + "\n…" + hint


def _render_required_one_of(fact: RequiredOneOf, advisory: str) -> str:
    attrs_str = ", ".join(sorted(fact.attrs))
    return f"at least one of: {attrs_str}{advisory}"


def _render_mutually_exclusive(fact: MutuallyExclusive, advisory: str) -> str:
    attrs_str = ", ".join(sorted(fact.attrs))
    return f"at most one of: {attrs_str}{advisory}"


def _render_mutually_exclusive_when(fact: MutuallyExclusiveWhen, advisory: str) -> str:
    attrs_str = ", ".join(sorted(fact.attrs))
    gate = "is true" if fact.when_true else "is set"
    return f"at most one of: {attrs_str} (when {fact.when_attr} {gate}){advisory}"


def _render_requires(fact: Requires, advisory: str) -> str:
    needs_str = ", ".join(sorted(fact.needs))
    if len(fact.needs) == 1:
        needs_str = list(fact.needs)[0]
    suffix = f" (when {fact.attr} is true)" if fact.when_true else ""
    return f"{fact.attr} requires {needs_str}{suffix}{advisory}"


def _render_requires_when_value(fact: RequiresWhenValue, advisory: str) -> str:
    values_str = ", ".join(sorted(fact.when_values))
    needs_str = ", ".join(sorted(fact.needs))
    unless = f" unless {', '.join(sorted(fact.unless))} is set" if fact.unless else ""
    return f"{fact.when_attr} in [{values_str}] requires {needs_str}{unless}{advisory}"


def _render_all_or_none(fact: AllOrNone, advisory: str) -> str:
    attrs_str = ", ".join(sorted(fact.attrs))
    return f"{attrs_str}: all together or none{advisory}"


def _render_forbids(fact: Forbids, advisory: str) -> str:
    excludes_str = ", ".join(sorted(fact.excludes))
    if fact.excludes_when_true:
        suffix = f" (when {fact.attr} is true, both true)" if fact.when_true else " (both true)"
    else:
        suffix = f" (when {fact.attr} is true)" if fact.when_true else ""
    return f"{fact.attr} cannot combine with: {excludes_str}{suffix}{advisory}"


def _render_forbids_when_value(fact: ForbidsWhenValue, advisory: str) -> str:
    values_str = ", ".join(sorted(fact.when_values))
    excludes_str = ", ".join(sorted(fact.excludes))
    return f"{fact.when_attr} in [{values_str}] cannot combine with: {excludes_str}{advisory}"


def _render_valid_values(fact: ValidValues, advisory: str) -> str:
    values = sorted(fact.values()) if callable(fact.values) else sorted(fact.values)
    values_str = ", ".join(values)
    return f"{fact.attr} must be one of: {values_str}{advisory}"


def _render_allowed_values_when(fact: AllowedValuesWhen, advisory: str) -> str:
    allowed = sorted(fact.allowed()) if callable(fact.allowed) else sorted(fact.allowed)
    allowed_str = ", ".join(allowed)
    suffix = f" (when {fact.when_attr} is true)" if fact.when_true else f" (when {fact.when_attr} is set)"
    return f"{fact.attr} must be one of: {allowed_str}{suffix}{advisory}"


_CONSTRAINT_RENDERERS: dict[type, object] = {
    RequiredOneOf: _render_required_one_of,
    MutuallyExclusive: _render_mutually_exclusive,
    MutuallyExclusiveWhen: _render_mutually_exclusive_when,
    Requires: _render_requires,
    RequiresWhenValue: _render_requires_when_value,
    AllOrNone: _render_all_or_none,
    Forbids: _render_forbids,
    ForbidsWhenValue: _render_forbids_when_value,
    ValidValues: _render_valid_values,
    AllowedValuesWhen: _render_allowed_values_when,
}


def _render_constraint_terse(fact: object) -> str:
    """Render a single constraint object as a terse one-liner for element_reference().

    Renders structural facts only (attr/attrs/needs/excludes/when_true); message is omitted.
    Attributes are sorted for stable output. lint_only facts are marked with [advisory].
    """
    advisory = " [advisory]" if getattr(fact, "lint_only", False) else ""
    renderer = _CONSTRAINT_RENDERERS.get(type(fact))
    if renderer is not None:
        return renderer(fact, advisory)  # type: ignore[operator]
    return f"<unknown constraint type: {type(fact).__name__}>{advisory}"


def overview_reference() -> str:
    """Describe the live discovery surface without loading a parallel guide."""

    topics = ", ".join(topic.value for topic in ReferenceTopic)
    categories = ", ".join(sorted({query.category.value for query in list_authoring_reference_queries()}))
    return (
        "# DATAMIMIC reference\n"
        f"Topics: {topics}.\n"
        "New models use the canonical AuthoringSpecV1 intent grammar. Query "
        "topic=authoring for its typed variants or topic=scaffold for the complete "
        "schema. Existing XML descriptors use the element, rules, context, targets, "
        "and distributions topics.\n"
        f"Authoring categories: {categories}."
    )


def _render_element_attributes(schema: ElementSchema, lines: list[str]) -> None:
    """Append attribute lines for one element schema to *lines*."""
    if schema.open_attrs:
        lines.append(
            "Attributes: open — credentials resolve from conf/{environment}.env.properties "
            "(keys {system}.{db|mongo}.{attr}); XML attributes override."
        )
    elif schema.attributes:
        lines.append("Attributes:")
        for spec in sorted(schema.attributes.values(), key=lambda s: (not s.required, s.name)):
            required = " (required)" if spec.required else ""
            default = "" if spec.default in (None, "") else f" [default: {spec.default}]"
            lines.append(f"- {spec.name}: {spec.annotation}{required}{default}")
            if spec.description:
                lines.append(f"    {spec.description}")
    else:
        lines.append("Attributes: none")


def _render_element_children(schema: ElementSchema, lines: list[str]) -> None:
    if schema.allowed_children is None:
        lines.append("Children: any element")
    elif schema.allowed_children:
        lines.append(f"Children: {', '.join(sorted(schema.allowed_children))}")
    else:
        lines.append("Children: none (leaf)")


def _render_element_source_capabilities(tag: str, lines: list[str]) -> None:
    source_facts = [capability for capability in source_capabilities() if capability.element == tag]
    if not source_facts:
        return
    lines.append("Source capabilities:")
    for capability in source_facts:
        context = f" type={capability.source_type}" if capability.source_type is not None else ""
        formats = ", ".join(file_format.value for file_format in capability.file_formats) or "none"
        lines.append(
            f"- source{context}: files [{formats}]; memstore={capability.allows_memstore}; "
            f"client={capability.allows_client}; "
            f"dynamic={capability.dynamic_source.value if capability.dynamic_source else 'none'}"
        )


def element_reference(tag: str) -> str:
    index = build_schema_index()
    canonical = canonical_tag(tag)
    # Alias schemas share canonical attributes/nesting but may add alias-specific
    # business rules (for example, <iterate> requires source=).
    schema = index.get(tag)
    if schema is None:
        raise ValueError(f"Unknown element '{tag}'. Known: {', '.join(sorted(index.tags))}")
    lines = [f"# <{canonical}>"]
    aliases = sorted(alias for alias, target in element_aliases().items() if target == canonical)
    if aliases:
        lines.append(f"Aliases: {', '.join(f'<{a}>' for a in aliases)}")
    _render_element_attributes(schema, lines)
    if schema.constraints:
        lines.append("Constraints:")
        for fact in schema.constraints:
            rendered = _render_constraint_terse(fact)
            lines.append(f"- {rendered}")
    _render_element_children(schema, lines)
    if schema.allowed_parents:
        lines.append(f"Allowed inside: {', '.join(sorted(schema.allowed_parents))}")
    _render_element_source_capabilities(tag, lines)
    return clip("\n".join(lines), 16000, " [truncated — inspect `datamimic capabilities` for the full schema]")


@lru_cache(maxsize=1)
def generator_reference() -> str:
    lines = ['# Generators (generator="Name" or generator="Name(arg=...)" )']
    package = importlib.import_module(_GENERATOR_PACKAGE)
    for module_info in sorted(pkgutil.iter_modules(package.__path__), key=lambda m: m.name):
        module = importlib.import_module(f"{_GENERATOR_PACKAGE}.{module_info.name}")
        for name, cls in sorted(vars(module).items()):
            if not (inspect.isclass(cls) and name.endswith("Generator") and cls.__module__ == module.__name__):
                continue
            try:
                # context/stmt/qualified_key are engine-injected, never DSL-passable - listing
                # them makes an agent write generator="SequenceTableGenerator(context=...)" and
                # hit a ValueError
                internal = ("self", "context", "stmt", "qualified_key")
                params = [p for p in inspect.signature(cls.__init__).parameters if p not in internal]
            except (TypeError, ValueError):
                params = []
            lines.append(f"- {name}({', '.join(params)})")
    return clip("\n".join(lines), 8000, " [truncated]")


def known_generator_names() -> set[str]:
    return {line[2:].split("(", 1)[0] for line in generator_reference().splitlines() if line.startswith("- ")}


def targets_reference() -> str:
    from datamimic_ce.exporters.exporter_util import buffered_exporter_names

    lines = [
        '# Targets (target="A, B")',
        f"File exporters: {', '.join(sorted(buffered_exporter_names()))} (exportUri= sets the output subdirectory)",
        f"Built-ins: {EXPORTER_CONSOLE_EXPORTER}, {EXPORTER_LOG_EXPORTER}, {EXPORTER_TEST_RESULT_EXPORTER}",
        "Declared ids: any <memstore id>, <database id>, <mongodb id> becomes a target name",
        "Client write ops: <clientId>.update / .upsert / .delete (e.g. mongodb.upsert); plain <clientId> inserts",
    ]
    return "\n".join(lines)


@lru_cache(maxsize=1)
def _entity_specs() -> dict[str, "EntitySpec"]:
    from datamimic_ce.domains.domain_core.entity_registry import list_entity_specs

    return {spec.entity: spec for spec in list_entity_specs()}


def entities_reference(name: str | None = None) -> str:
    """Enumerate the built-in domain entities (entity="Name" on <variable>/<key>)."""
    specs = _entity_specs()
    if not name:
        return (
            '# Entities (use as <variable name="p" entity="Person" dataset="DE" locale="de"/> then '
            'script="p.field")\n'
            + ", ".join(sorted(specs))
            + "\n\nCall topic=entities name=<Entity> for its fields. Fields resolve case/underscore-"
            "insensitively (givenName == given_name)."
        )
    spec = specs.get(name) or specs.get(name.capitalize())
    if spec is None:
        raise ValueError(f"Unknown entity '{name}'. Known: {', '.join(sorted(specs))}")
    lines = [f'# entity="{spec.entity}" fields (access via script="<var>.<field>")']
    for field in spec.attributes:
        opt = "?" if field.optional else ""
        nested = " {…}" if field.children else ""
        lines.append(f"- {field.name}{opt}: {field.py_type}{nested}")
    return clip("\n".join(lines), 4000, " [truncated — see topic=entities for the full list]")


def context_reference() -> str:
    """Script/expression scope: fields by bare name plus the this/parent/root aliases."""
    return (
        '# Script scope (script=, condition=, count="{expr}") — plain Python\n'
        "- Fields and <variable>s of the CURRENT record are referenced by BARE name: "
        'script="given_name", script="age * 2".\n'
        "- `this.<field>`  — the current scope explicitly; `this.x` == bare `x`. Use it in a nested "
        "<nestedKey>/<list> scope where a bare sibling name is wrapped under the scope name and would "
        "not resolve.\n"
        "- `parent.<field>` — the immediate parent <generate>/<nestedKey> scope (a child reading its "
        "parent's fields, e.g. parent.customer_id).\n"
        "- `root.<field>` / `root.<name>.<field>` — the outermost record's merged fields.\n"
        "- A <variable> result is dot-accessed: person.given_name (NOT person['given_name'], NOT "
        "__person__ — that is string= interpolation, see DM314).\n"
        "- Properties from <include> .properties files are in scope by their key."
    )


def timeseries_reference() -> str:
    """<generate start/end/interval> time-series mode + the ts script namespace."""
    return (
        "# Time-series <generate start=... end=... interval=...>\n"
        "- start/end are ISO datetimes, interval an ISO 8601 duration (PT1H, P1D). All three "
        "together turn a <generate> into a time-series iterator; a partial set is a parse error, "
        "and end must be after start.\n"
        "- count = number of SERIES (default 1). Total rows = count x ticks_per_series, where "
        "ticks_per_series = floor((end - start) / interval).\n"
        "- Each tick exposes a read-only `ts` object to script= / condition=:\n"
        "    ts.now    - datetime of this tick\n"
        "    ts.step   - 0..ticks_per_series-1 within the current series\n"
        "    ts.series - 0..count-1 (which series)\n"
        "- ts.* is reproducible without rngSeed (time is deterministic). Avoid naming a "
        "<variable> 'ts' in this mode.\n"
        '- Example: <generate name="readings" start="2025-01-01T00:00:00" '
        'end="2025-01-02T00:00:00" interval="PT1H" count="3" target="JSON">'
        '<key name="at" script="ts.now"/><key name="sensor" script="ts.series"/></generate>'
    )


def distributions_reference() -> str:
    from datamimic_ce.enums.distribution_enums import (
        POSITIONAL_NUMBER_SEQUENCES,
    )

    members = ", ".join(sorted(resolved_values(SOURCE_DISTRIBUTION_VALUES)))
    numeric = ", ".join(sorted(resolved_values(KEY_DISTRIBUTION_VALUES)))
    finite_sequences = ", ".join(member.value for member in POSITIONAL_NUMBER_SEQUENCES)
    source_matrix = "\n".join(
        f"- <{fact.element}>{f' type={fact.source_type}' if fact.source_type else ''}: "
        f"files [{', '.join(file_format.value for file_format in fact.file_formats) or 'none'}], "
        f"memstore={fact.allows_memstore}, client={fact.allows_client}, "
        f"dynamic={fact.dynamic_source.value if fact.dynamic_source else 'none'}"
        for fact in source_capabilities()
    )
    return (
        f"# distribution= on source reads ({members})\n"
        "- ABSENT defaults to RANDOM (shuffled permutation), NOT source order (DM301)\n"
        "- ordered: sequential, reads page by page — the only memory-bounded mode (DM302)\n"
        "- random: one seeded global shuffle; pages/workers take disjoint windows\n"
        "- cumulated: bell-weighted picks WITH replacement (middle of load order favored)\n"
        '- unique="True": distinct rows without replacement; pool must cover the count\n'
        '- reproducibility: <setup rngSeed="N"> replays identically and forces single process '
        "(DM303/DM304); unseeded runs differ by design\n"
        f"\n# distribution= on numeric range keys ({numeric})\n"
        "- uniform: default per-row random draw across the numeric range\n"
        "- cumulated: per-row bell-shaped draw (mean = midpoint), not a source read\n"
        "- step/increment: min, min+d, min+2d, ... until max; finite, no wrapping\n"
        "- shuffle: deterministic strided walk over the range grid; finite, unique until exhausted\n"
        "- wedge: min, max, min+d, max-d, ... converging toward the middle; finite\n"
        "- bitreverse: bit-reversed counter order over the range grid; finite\n"
        "- fibonacci/padovan: recurrence values clipped to [min,max]; finite\n"
        "- randomWalk: seeded bounded walk that starts at min and saturates at max\n"
        f"- multiprocessing: finite positional sequences ({finite_sequences}) are rejected because "
        "worker-local iterator state would duplicate values; use single-process or a per-row draw\n"
        '- numeric range fields only (type int/float/decimal with min/max); type="string" or a '
        "missing range fails at parse time\n"
        '- Examples: <key name="id" type="int" min="1" max="100" distribution="step"/>; '
        '<key name="amount" type="decimal" min="0.01" max="9.99" granularity="0.01" '
        'distribution="wedge"/>\n'
        "\n# source= capabilities by runtime context\n"
        f"{source_matrix}"
    )


def converters_reference() -> str:
    from datamimic_ce.enums.converter_enums import ConverterEnum

    names = ", ".join(sorted(member.value for member in ConverterEnum))
    return (
        "# Converters (converter= on <key>/<variable>; chain with ';')\n"
        f"Built-in: {names}\n"
        "- Applied to the field value after generation, e.g. "
        '<key name="email" script="p.email" converter="Mask"/>\n'
        '- Arguments use constructor syntax: converter="CutLength(10)" or "Append(\'_test\')"\n'
        "- Substring(start[, end]) uses Python slice semantics; negative indexes count from "
        'the end: converter="Substring(-4)" keeps the last 4 chars (the classic anonymization '
        'tail-extract), "Substring(5, 8)" a window, "Substring(2)" from index 2 to the end.\n'
        "- Custom: subclass datamimic_ce.converter.converter.Converter in a .py file, load it "
        'with <execute uri="script/my_converters.scr.py"/>, then converter="MyConverter()" '
        "(same mechanism for custom generators)."
    )


def rules_reference(name: str | None = None) -> str:
    """Project the public rule catalog without maintaining a prose copy."""
    if name is None:
        lines = ["# Authoring rules (topic=rules name=DMxxx for details)"]
        lines.extend(
            f"- {definition.id} [{definition.severity.value}]: {definition.title}"
            for definition in authoring_rule_definitions()
        )
        return clip("\n".join(lines), 12000, " [truncated — query one rule by id]")
    rule_id = name.upper()
    try:
        definition = authoring_rule_definition(rule_id)
    except KeyError as err:
        known = ", ".join(definition.id for definition in authoring_rule_definitions())
        raise ValueError(f"Unknown rule '{name}'. Known: {known}") from err
    return (
        f"# {definition.id}: {definition.title}\n"
        f"Severity: {definition.severity.value}\n"
        f"Explanation: {definition.explanation}\n"
        f"Fix: {definition.fix_hint}\n"
        f"Provenance: {definition.provenance}\n"
        f"Valid: {definition.valid_example}\n"
        f"Invalid: {definition.invalid_example}"
    )


def scaffold_reference() -> str:
    """Versioned intent schema projected directly from the Intent SPOT."""
    from datamimic_ce.authoring.spec import authoring_spec_json_schema

    return (
        "# AuthoringSpecV1 (model.dm.json)\n"
        "Pass a versioned intent document to `datamimic scaffold <path|-> --format json`. "
        "Unknown and unsupported intent is rejected by the canonical Pydantic grammar.\n\n"
        "## JSON Schema\n```json\n"
        f"{json.dumps(authoring_spec_json_schema(), indent=2)}\n```"
    )


def compact_authoring_reference(query: AuthoringReferenceQuery | None = None) -> str:
    """Render one compact, enum-addressed projection from the Intent Model SPOT."""

    if query is None:
        return json.dumps(
            {
                "topic": ReferenceTopic.AUTHORING,
                "queries": [candidate.model_dump(mode="json") for candidate in list_authoring_reference_queries()],
                "usage": "reference authoring --category <category> --kind <kind>",
            },
            indent=2,
        )
    return authoring_reference_projection(query).model_dump_json(indent=2)


def capabilities_manifest() -> dict[str, Any]:
    """Machine-readable DSL surface, derived live from the engine registries — cannot drift."""
    from importlib.metadata import PackageNotFoundError, version

    from datamimic_ce.authoring.spec import authoring_spec_json_schema
    from datamimic_ce.enums.converter_enums import ConverterEnum
    from datamimic_ce.enums.distribution_enums import POSITIONAL_NUMBER_SEQUENCES
    from datamimic_ce.exporters.exporter_util import buffered_exporter_names

    try:
        schema_version = version("datamimic_ce")
    except PackageNotFoundError:
        # Editable/dev checkout without an installed distribution metadata record.
        schema_version = None

    index = build_schema_index()
    elements: dict[str, Any] = {}
    for tag, schema in sorted(index.elements.items()):
        elements[tag] = {
            "attributes": {
                spec.name: {
                    "required": spec.required,
                    "type": spec.annotation,
                    **({"description": spec.description} if spec.description else {}),
                }
                for spec in sorted(schema.attributes.values(), key=lambda s: s.name)
            },
            "children": sorted(schema.allowed_children) if schema.allowed_children is not None else "any",
            **({"constraints": serialize_constraints(schema.constraints)} if schema.constraints else {}),
        }
    return {
        "schema_version": schema_version,
        "elements": elements,
        "aliases": element_aliases(),
        "generators": sorted(known_generator_names()),
        "entities": sorted(_entity_specs()),
        "converters": sorted(member.value for member in ConverterEnum),
        "targets": {
            "file_exporters": sorted(buffered_exporter_names()),
            "built_ins": [EXPORTER_CONSOLE_EXPORTER, EXPORTER_LOG_EXPORTER],
            "declared_ids": "any <memstore>/<database>/<mongodb> id; client write ops: <id>.update/.upsert/.delete",
        },
        "distributions": sorted(resolved_values(SOURCE_DISTRIBUTION_VALUES)),
        "numeric_distributions": sorted(resolved_values(KEY_DISTRIBUTION_VALUES)),
        "finite_numeric_sequences": sorted(member.value for member in POSITIONAL_NUMBER_SEQUENCES),
        "source_capabilities": [serialize_source_capability(capability) for capability in source_capabilities()],
        "rules": [serialize_rule_definition(definition) for definition in authoring_rule_definitions()],
        "authoring_spec": authoring_spec_json_schema(),
    }


_TOPIC_HANDLERS: dict[ReferenceTopic, object] = {
    ReferenceTopic.OVERVIEW: lambda _n, _q: overview_reference(),
    ReferenceTopic.ELEMENT: lambda name, _q: _element_ref_require_name(name),
    ReferenceTopic.GENERATORS: lambda name, _q: _generator_ref_filter(generator_reference(), name),
    ReferenceTopic.ENTITIES: lambda name, _q: entities_reference(name),
    ReferenceTopic.CONTEXT: lambda _n, _q: context_reference(),
    ReferenceTopic.TIMESERIES: lambda _n, _q: timeseries_reference(),
    ReferenceTopic.TARGETS: lambda _n, _q: targets_reference(),
    ReferenceTopic.DISTRIBUTIONS: lambda _n, _q: distributions_reference(),
    ReferenceTopic.CONVERTERS: lambda _n, _q: converters_reference(),
    ReferenceTopic.RULES: lambda name, _q: rules_reference(name),
    ReferenceTopic.SCAFFOLD: lambda _n, _q: scaffold_reference(),
    ReferenceTopic.AUTHORING: lambda _n, query: compact_authoring_reference(query),
}


def _element_ref_require_name(name: str | None) -> str:
    if not name:
        raise ValueError("topic=element needs name=<tag>")
    return element_reference(name)


def _generator_ref_filter(text: str, name: str | None) -> str:
    if not name:
        return text
    matches = [line for line in text.splitlines() if name.lower() in line.lower()]
    return "\n".join(matches) if matches else f"No generator matching '{name}'."


def reference(
    topic: ReferenceTopic,
    name: str | None = None,
    *,
    query: AuthoringReferenceQuery | None = None,
) -> str:
    handler = _TOPIC_HANDLERS.get(topic)
    if handler is not None:
        return handler(name, query)  # type: ignore[operator]
    raise ValueError(f"Unknown topic '{topic}'. Topics: {', '.join(ReferenceTopic)}")
