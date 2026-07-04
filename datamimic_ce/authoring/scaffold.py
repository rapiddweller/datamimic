# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Render a DATAMIMIC descriptor from a compact JSON spec.

Weak LLMs fail at STRUCTURE (well-formed XML, valid element/attribute names) far
more than at VALUES. This renders guaranteed-structurally-valid DSL from a small
JSON spec, so the model only chooses field values/kinds — never touches XML
syntax or element names. The model can emit the spec under a JSON schema
(SPEC_JSON_SCHEMA) via structured output, eliminating DM001/DM101/DM103/DM104 at
the source. Semantic wiring (does a referenced memstore get populated?) is still
the author's job — but the linter now catches that.
"""

from typing import Any
from xml.sax.saxutils import quoteattr

# Leaf field kinds (a single value); nested_list is a top-level-only container kind.
_LEAF_KINDS = [
    "increment", "person_name", "person_email", "int_range", "float_range",
    "decimal_range", "string_length", "values", "weighted", "pattern", "constant", "script",
]
_FIELD_KINDS = [*_LEAF_KINDS, "nested_list"]


def _field_schema(kinds: list[str], allow_children: bool) -> dict[str, Any]:
    """One field object. FLAT (no $ref): a local constrained-decoding runtime — Ollama's
    format=, llama.cpp's json-schema-to-GBNF — silently drops recursive $ref, so nesting is
    inlined to a fixed depth (top field -> optional leaf children) instead of self-referencing."""
    props: dict[str, Any] = {
        "name": {"type": "string"},
        "kind": {"type": "string", "enum": kinds},
        "min": {"type": "number"},
        "max": {"type": "number"},
        "values": {"type": "array", "items": {"type": "string"}},
        "weights": {"type": "array", "items": {"type": "number"}},
        "pattern": {"type": "string"},
        "value": {"type": "string"},
        "script": {"type": "string"},
    }
    if allow_children:
        # nested_list children are leaves only — one level of nesting, no recursion.
        props["fields"] = {"type": "array", "items": _field_schema(_LEAF_KINDS, allow_children=False)}
    return {"type": "object", "properties": props, "required": ["name", "kind"]}


# JSON schema the model fills (pass as Ollama `format=` / structured output). No $ref.
SPEC_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "seed": {"type": "integer"},
        "generates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "count": {"type": "integer"},
                    "target": {"type": "string", "description": "e.g. JSON, CSV, or a memstore id"},
                    "fields": {"type": "array", "items": _field_schema(_FIELD_KINDS, allow_children=True)},
                },
                "required": ["name", "fields"],
            },
        },
    },
    "required": ["generates"],
}

_ENTITY_VAR = "_ent_person"  # single shared Person variable when person_* fields appear

# Local constrained-decoding runtimes (Ollama format=) don't strictly enforce the schema —
# models emit near-miss keys. Normalize the common drift so a semantically-correct spec renders.
_KIND_ALIASES = {
    "id": "increment", "auto": "increment", "sequence": "increment", "autoincrement": "increment",
    "name": "person_name", "fullname": "person_name", "full_name": "person_name", "person": "person_name",
    "email": "person_email",
    "int": "int_range", "integer": "int_range", "number": "int_range", "number_range": "int_range",
    "float": "float_range", "decimal": "decimal_range", "money": "decimal_range",
    "string": "string_length", "str": "string_length", "text": "string_length",
    "enum": "values", "choice": "values", "choices": "values", "categorical": "values", "category": "values",
    "weighted_values": "weighted", "weighted values": "weighted", "weighted_choice": "weighted",
    "regex": "pattern", "const": "constant", "fixed": "constant",
    "expression": "script", "formula": "script", "computed": "script",
    "nested": "nested_list", "list": "nested_list", "array": "nested_list", "object": "nested_list",
}
_FILE_TARGET = {".json": "JSON", ".csv": "CSV", ".xml": "XML", ".xlsx": "XLSX", ".txt": "TXT"}


def _norm_kind(kind: object) -> str:
    k = str(kind or "constant").strip().lower()
    return k if k in _FIELD_KINDS else _KIND_ALIASES.get(k, "constant")


def _norm_target(target: object) -> str:
    t = str(target or "JSON").strip()
    for ext, fmt in _FILE_TARGET.items():
        if t.lower().endswith(ext):
            return fmt
    return t  # a format keyword, memstore id, or client id — leave as-is


def _normalize(spec: dict[str, Any]) -> dict[str, Any]:
    """Map a model's near-miss JSON onto the canonical spec shape (generate->generates,
    weighted_values->weighted, 'x.json' target->JSON, kind/type & name/field aliases)."""
    gens = spec.get("generates") or spec.get("generate") or spec.get("entities") or []
    if isinstance(gens, dict):
        gens = [gens]

    def _field(f: dict[str, Any]) -> dict[str, Any]:
        out = dict(f)
        out["name"] = f.get("name") or f.get("field") or f.get("column") or "field"
        out["kind"] = _norm_kind(f.get("kind") or f.get("type"))
        children = f.get("fields") or f.get("children")
        if children:
            out["kind"] = "nested_list"
            out["fields"] = [_field(c) for c in children if isinstance(c, dict)]
        return out

    norm_gens = []
    for gen in gens:
        if not isinstance(gen, dict):
            continue
        fields = gen.get("fields") or gen.get("keys") or gen.get("columns") or []
        norm_gens.append({
            "name": gen.get("name") or "data",
            "count": gen.get("count"),
            "target": _norm_target(gen.get("target")),
            "fields": [_field(f) for f in fields if isinstance(f, dict)],
        })
    return {"seed": spec.get("seed"), "generates": norm_gens}


def _quote_values(values: list[str]) -> str:
    return ", ".join("'" + str(v).replace("'", "\\'") + "'" for v in values)


def _render_field(field: dict[str, Any], indent: str) -> list[str]:
    name = field["name"]
    kind = field.get("kind", "constant")
    a = f'name={quoteattr(name)}'
    if kind == "increment":
        return [f'{indent}<key {a} generator="IncrementGenerator"/>']
    if kind == "person_name":
        return [f'{indent}<key {a} script="{_ENTITY_VAR}.name"/>']
    if kind == "person_email":
        return [f'{indent}<key {a} script="{_ENTITY_VAR}.email"/>']
    if kind == "int_range":
        return [f'{indent}<key {a} type="int" min="{int(field.get("min", 0))}" max="{int(field.get("max", 100))}"/>']
    if kind == "float_range":
        return [f'{indent}<key {a} type="float" min="{field.get("min", 0)}" max="{field.get("max", 1)}"/>']
    if kind == "decimal_range":
        return [f'{indent}<key {a} type="decimal" min="{field.get("min", 0)}" max="{field.get("max", 1000)}"/>']
    if kind == "string_length":
        return [f'{indent}<key {a} type="string" minLength="{int(field.get("min", 4))}" '
                f'maxLength="{int(field.get("max", 12))}"/>']
    if kind == "values":
        return [f'{indent}<key {a} values={quoteattr(_quote_values(field.get("values", [])))}/>']
    if kind == "weighted":
        weights = ",".join(str(w) for w in field.get("weights", []))
        return [f'{indent}<key {a} values={quoteattr(_quote_values(field.get("values", [])))} '
                f'weights={quoteattr(weights)}/>']
    if kind == "pattern":
        return [f'{indent}<key {a} pattern={quoteattr(field.get("pattern", "[A-Z]{3}"))}/>']
    if kind == "constant":
        return [f'{indent}<key {a} constant={quoteattr(str(field.get("value", "")))}/>']
    if kind == "script":
        return [f'{indent}<key {a} script={quoteattr(field.get("script", ""))}/>']
    if kind == "nested_list":
        lo, hi = int(field.get("min", 1)), int(field.get("max", 3))
        lines = [f'{indent}<nestedKey {a} type="list" minCount="{lo}" maxCount="{hi}">']
        for sub in field.get("fields", []):
            lines += _render_field(sub, indent + "    ")
        lines.append(f"{indent}</nestedKey>")
        return lines
    # unknown kind -> a safe constant so structure stays valid
    return [f'{indent}<key {a} constant={quoteattr(str(field.get("value", "")))}/>']


def _uses_person(fields: list[dict[str, Any]]) -> bool:
    return any(
        f.get("kind", "").startswith("person_") or _uses_person(f.get("fields", [])) for f in fields
    )


def render(spec: dict[str, Any]) -> str:
    """Render a spec dict into a structurally-valid DATAMIMIC descriptor string.

    Tolerant of a model's near-miss key drift (see _normalize). Raises ValueError only
    when there is genuinely no generate to render — never a silently-empty descriptor.
    """
    spec = _normalize(spec)
    generates = spec["generates"]
    if not generates or not any(g["fields"] for g in generates):
        raise ValueError(
            "spec needs a non-empty 'generates' list with fields, e.g. "
            "{'generates': [{'name': 'x', 'count': 10, 'fields': [{'name': 'id', 'kind': 'increment'}]}]}"
        )

    seed = spec.get("seed")
    setup_open = f'<setup rngSeed="{int(seed)}">' if seed is not None else "<setup>"
    lines = [setup_open]

    # Declare any memstore referenced as a target so DM402 stays clean.
    memstore_ids = {
        t.strip()
        for g in spec.get("generates", [])
        for t in str(g.get("target", "")).split(",")
        if t.strip() and t.strip() not in {"JSON", "CSV", "XML", "XLSX", "TXT", "DbUnit",
                                           "ConsoleExporter", "LogExporter"}
    }
    for mid in sorted(memstore_ids):
        lines.append(f'    <memstore id={quoteattr(mid)}/>')

    for gen in spec.get("generates", []):
        fields = gen.get("fields", [])
        attrs = f'name={quoteattr(gen["name"])}'
        if gen.get("count") is not None:
            attrs += f' count="{int(gen["count"])}"'
        if gen.get("target"):
            attrs += f' target={quoteattr(gen["target"])}'
        lines.append(f"    <generate {attrs}>")
        if _uses_person(fields):
            lines.append(f'        <variable name="{_ENTITY_VAR}" entity="Person"/>')
        for field in fields:
            lines += _render_field(field, "        ")
        lines.append("    </generate>")

    lines.append("</setup>")
    return "\n".join(lines)
