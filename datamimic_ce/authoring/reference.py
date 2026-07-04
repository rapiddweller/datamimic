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
        "Client operations: <clientId>.upsert / <clientId>.delete (e.g. mongodb.upsert)",
    ]
    return "\n".join(lines)


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
    if topic == "targets":
        return targets_reference()
    if topic == "distributions":
        return distributions_reference()
    if topic == "recipes":
        return list_recipes()
    if topic == "recipe":
        if not name:
            raise ValueError("topic=recipe needs name=<recipe id>. " + list_recipes())
        return load_recipe(name)
    raise ValueError(
        f"Unknown topic '{topic}'. Topics: overview, element, generators, targets, distributions, "
        "recipes, recipe"
    )
