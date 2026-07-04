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

# JSON schema the model fills (pass as Ollama `format=` / structured output).
_FIELD_KINDS = [
    "increment", "person_name", "person_email", "int_range", "float_range",
    "decimal_range", "string_length", "values", "weighted", "pattern",
    "constant", "script", "nested_list",
]
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
                    "fields": {"type": "array", "items": {"$ref": "#/$defs/field"}},
                },
                "required": ["name", "fields"],
            },
        },
    },
    "required": ["generates"],
    "$defs": {
        "field": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "kind": {"type": "string", "enum": _FIELD_KINDS},
                "min": {"type": "number"},
                "max": {"type": "number"},
                "values": {"type": "array", "items": {"type": "string"}},
                "weights": {"type": "array", "items": {"type": "number"}},
                "pattern": {"type": "string"},
                "value": {"type": "string"},
                "script": {"type": "string"},
                "fields": {"type": "array", "items": {"$ref": "#/$defs/field"}},
            },
            "required": ["name", "kind"],
        }
    },
}

_ENTITY_VAR = "_ent_person"  # single shared Person variable when person_* fields appear


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

    Raises ValueError on a spec that does not match SPEC_JSON_SCHEMA's shape, so a
    malformed spec is a clear error — never a silently-empty descriptor.
    """
    generates = spec.get("generates")
    if not isinstance(generates, list) or not generates:
        raise ValueError(
            "spec needs a non-empty 'generates' list, e.g. "
            "{'generates': [{'name': 'x', 'count': 10, 'fields': [{'name': 'id', 'kind': 'increment'}]}]}"
        )
    for gen in generates:
        if not isinstance(gen, dict) or "name" not in gen or not isinstance(gen.get("fields"), list):
            raise ValueError(f"each generate needs 'name' and a 'fields' list; got {gen!r}")

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
