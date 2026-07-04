# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""DSL reference for agents: element schemas, generators, targets, distributions,
recipes — everything derived from the engine's registries or gate-tested content.
Token-capped: every answer ends with a pointer instead of overflowing."""

import importlib
import inspect
import pkgutil
import tomllib
from functools import lru_cache
from importlib import resources
from typing import Any

from datamimic_ce.authoring.schema import ALIASES, build_schema_index
from datamimic_ce.constants.exporter_constants import (
    EXPORTER_CONSOLE_EXPORTER,
    EXPORTER_LOG_EXPORTER,
    EXPORTER_TEST_RESULT_EXPORTER,
)
from datamimic_ce.enums.distribution_enums import SourceDistribution

_GENERATOR_PACKAGE = "datamimic_ce.domains.common.literal_generators"


def clip(text: str, max_chars: int, hint: str) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - len(hint) - 2].rstrip() + "\n…" + hint


@lru_cache(maxsize=1)
def cheatsheet() -> str:
    return (resources.files("datamimic_ce.authoring") / "reference_data" / "cheatsheet.md").read_text(
        encoding="utf-8"
    )


def element_reference(tag: str) -> str:
    index = build_schema_index()
    canonical = ALIASES.get(tag, tag)
    schema = index.get(canonical)
    if schema is None:
        raise ValueError(f"Unknown element '{tag}'. Known: {', '.join(sorted(index.tags))}")
    lines = [f"# <{canonical}>"]
    aliases = sorted(alias for alias, target in ALIASES.items() if target == canonical)
    if aliases:
        lines.append(f"Aliases: {', '.join(f'<{a}>' for a in aliases)}")
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
    else:
        lines.append("Attributes: none")
    if schema.allowed_children is None:
        lines.append("Children: any element")
    elif schema.allowed_children:
        lines.append(f"Children: {', '.join(sorted(schema.allowed_children))}")
    else:
        lines.append("Children: none (leaf)")
    if schema.allowed_parents:
        lines.append(f"Allowed inside: {', '.join(sorted(schema.allowed_parents))}")
    return clip(
        "\n".join(lines), 4000, " [truncated — ask for a specific attribute or see the cheatsheet]"
    )


@lru_cache(maxsize=1)
def generator_reference() -> str:
    lines = ["# Generators (generator=\"Name\" or generator=\"Name(arg=...)\" )"]
    package = importlib.import_module(_GENERATOR_PACKAGE)
    for module_info in sorted(pkgutil.iter_modules(package.__path__), key=lambda m: m.name):
        module = importlib.import_module(f"{_GENERATOR_PACKAGE}.{module_info.name}")
        for name, cls in sorted(vars(module).items()):
            if not (inspect.isclass(cls) and name.endswith("Generator") and cls.__module__ == module.__name__):
                continue
            try:
                params = [p for p in inspect.signature(cls.__init__).parameters if p not in ("self",)]
            except (TypeError, ValueError):
                params = []
            lines.append(f"- {name}({', '.join(params)})")
    return clip("\n".join(lines), 8000, " [truncated]")


def known_generator_names() -> set[str]:
    return {line[2:].split("(", 1)[0] for line in generator_reference().splitlines() if line.startswith("- ")}


def targets_reference() -> str:
    from datamimic_ce.exporters.exporter_util import _BUFFERED_EXPORTERS

    lines = [
        "# Targets (target=\"A, B\")",
        f"File exporters: {', '.join(sorted(_BUFFERED_EXPORTERS))} "
        "(exportUri= sets the output subdirectory)",
        f"Built-ins: {EXPORTER_CONSOLE_EXPORTER}, {EXPORTER_LOG_EXPORTER}, {EXPORTER_TEST_RESULT_EXPORTER}",
        "Declared ids: any <memstore id>, <database id>, <mongodb id> becomes a target name",
        "Client write ops: <clientId>.update / .upsert / .delete (e.g. mongodb.upsert); "
        "plain <clientId> inserts",
    ]
    return "\n".join(lines)


@lru_cache(maxsize=1)
def _entity_specs() -> dict[str, Any]:
    from datamimic_ce.domains.domain_core.entity_registry import list_entity_specs

    return {spec.entity: spec for spec in list_entity_specs()}


def entities_reference(name: str | None = None) -> str:
    """Enumerate the built-in domain entities (entity="Name" on <variable>/<key>)."""
    specs = _entity_specs()
    if not name:
        return (
            "# Entities (use as <variable name=\"p\" entity=\"Person\" dataset=\"DE\" locale=\"de\"/> then "
            "script=\"p.field\")\n"
            + ", ".join(sorted(specs))
            + "\n\nCall topic=entities name=<Entity> for its fields. Fields resolve case/underscore-"
            "insensitively (givenName == given_name)."
        )
    spec = specs.get(name) or specs.get(name.capitalize())
    if spec is None:
        raise ValueError(f"Unknown entity '{name}'. Known: {', '.join(sorted(specs))}")
    lines = [f"# entity=\"{spec.entity}\" fields (access via script=\"<var>.<field>\")"]
    for field in spec.attributes:
        opt = "?" if getattr(field, "optional", False) else ""
        nested = " {…}" if getattr(field, "children", None) else ""
        lines.append(f"- {field.name}{opt}: {field.py_type}{nested}")
    return clip("\n".join(lines), 4000, " [truncated — see topic=entities for the full list]")


def context_reference() -> str:
    """Script/expression scope: fields by bare name plus the this/parent/root aliases."""
    return (
        "# Script scope (script=, condition=, count=\"{expr}\") — plain Python\n"
        "- Fields and <variable>s of the CURRENT record are referenced by BARE name: "
        "script=\"given_name\", script=\"age * 2\".\n"
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
        "- Example: <generate name=\"readings\" start=\"2025-01-01T00:00:00\" "
        "end=\"2025-01-02T00:00:00\" interval=\"PT1H\" count=\"3\" target=\"JSON\">"
        "<key name=\"at\" script=\"ts.now\"/><key name=\"sensor\" script=\"ts.series\"/></generate>"
    )


def distributions_reference() -> str:
    members = ", ".join(member.value for member in SourceDistribution)
    return (
        f"# distribution= on source reads ({members})\n"
        "- ABSENT defaults to RANDOM (shuffled permutation), NOT source order (DM301)\n"
        "- ordered: sequential, reads page by page — the only memory-bounded mode (DM302)\n"
        "- random: one seeded global shuffle; pages/workers take disjoint windows\n"
        "- cumulated: bell-weighted picks WITH replacement (middle of load order favored)\n"
        "- unique=\"True\": distinct rows without replacement; pool must cover the count\n"
        "- reproducibility: <setup rngSeed=\"N\"> replays identically and forces single process "
        "(DM303/DM304); unseeded runs differ by design"
    )


def converters_reference() -> str:
    from datamimic_ce.enums.converter_enums import ConverterEnum

    names = ", ".join(sorted(member.value for member in ConverterEnum))
    return (
        "# Converters (converter= on <key>/<variable>; chain with ';')\n"
        f"Built-in: {names}\n"
        "- Applied to the field value after generation, e.g. "
        "<key name=\"email\" script=\"p.email\" converter=\"Mask\"/>\n"
        "- Arguments use constructor syntax: converter=\"CutLength(10)\" or \"Append('_test')\"\n"
        "- Custom: subclass datamimic_ce.converter.converter.Converter in a .py file, load it "
        "with <execute uri=\"script/my_converters.scr.py\"/>, then converter=\"MyConverter()\" "
        "(same mechanism for custom generators)."
    )


def capabilities_manifest() -> dict[str, Any]:
    """Machine-readable DSL surface, derived live from the engine registries — cannot drift."""
    from datamimic_ce.enums.converter_enums import ConverterEnum
    from datamimic_ce.exporters.exporter_util import _BUFFERED_EXPORTERS

    index = build_schema_index()
    elements: dict[str, Any] = {}
    for tag, schema in sorted(index.elements.items()):
        elements[tag] = {
            "attributes": {
                spec.name: {"required": spec.required, "type": spec.annotation}
                for spec in sorted(schema.attributes.values(), key=lambda s: s.name)
            },
            "children": sorted(schema.allowed_children) if schema.allowed_children is not None else "any",
        }
    return {
        "elements": elements,
        "aliases": dict(ALIASES),
        "generators": sorted(known_generator_names()),
        "entities": sorted(_entity_specs()),
        "converters": sorted(member.value for member in ConverterEnum),
        "targets": {
            "file_exporters": sorted(_BUFFERED_EXPORTERS),
            "built_ins": [EXPORTER_CONSOLE_EXPORTER, EXPORTER_LOG_EXPORTER],
            "declared_ids": "any <memstore>/<database>/<mongodb> id; client write ops: <id>.update/.upsert/.delete",
        },
        "distributions": [member.value for member in SourceDistribution],
    }


@lru_cache(maxsize=1)
def _recipes_index() -> dict[str, list[dict[str, Any]]]:
    raw = (resources.files("datamimic_ce.authoring") / "recipes" / "recipes.toml").read_text(encoding="utf-8")
    return tomllib.loads(raw)


def list_recipes() -> str:
    lines = ["# Recipes (topic=recipe name=<id> for the full descriptor)"]
    for recipe in _recipes_index()["recipe"]:
        lines.append(f"- {recipe['id']}: {recipe['summary']} [elements: {', '.join(recipe['elements'])}]")
    return "\n".join(lines)


def load_recipe(recipe_id: str) -> str:
    entries = {recipe["id"]: recipe for recipe in _recipes_index()["recipe"]}
    if recipe_id not in entries:
        raise ValueError(f"Unknown recipe '{recipe_id}'. Known: {', '.join(sorted(entries))}")
    xml = (resources.files("datamimic_ce.authoring") / "recipes" / f"{recipe_id}.xml").read_text(
        encoding="utf-8"
    )
    entry = entries[recipe_id]
    return f"# {entry['title']}\n{entry['summary']}\n\n```xml\n{xml}```"


def reference(topic: str, name: str | None = None) -> str:
    if topic == "overview":
        return clip(cheatsheet(), 16000, " [truncated — ask a specific topic]")
    if topic == "element":
        if not name:
            raise ValueError("topic=element needs name=<tag>")
        return element_reference(name)
    if topic == "generators":
        text = generator_reference()
        if name:
            matches = [line for line in text.splitlines() if name.lower() in line.lower()]
            return "\n".join(matches) if matches else f"No generator matching '{name}'."
        return text
    if topic == "entities":
        return entities_reference(name)
    if topic == "context":
        return context_reference()
    if topic == "timeseries":
        return timeseries_reference()
    if topic == "targets":
        return targets_reference()
    if topic == "distributions":
        return distributions_reference()
    if topic == "converters":
        return converters_reference()
    if topic == "recipes":
        return list_recipes()
    if topic == "recipe":
        if not name:
            raise ValueError("topic=recipe needs name=<recipe id>. " + list_recipes())
        return load_recipe(name)
    raise ValueError(
        f"Unknown topic '{topic}'. Topics: overview, element, generators, entities, context, "
        "timeseries, targets, distributions, converters, recipes, recipe"
    )
