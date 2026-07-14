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

import ast
import re
from dataclasses import dataclass
from typing import Any
from xml.sax.saxutils import quoteattr

from datamimic_ce.authoring.schema import element_json_schema

# Matches a fake fallback function the model invents when it hasn't discovered the real
# unique= property (observed: kind="script", script="random.unique(1, 180)") — extracts
# the two numeric bounds so the field can still be converted to a real int_range+unique.
_UNIQUE_RANGE_SCRIPT_RE = re.compile(r"unique\w*\s*\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)", re.IGNORECASE)

# Leaf field kinds (a single value); nested_list is a top-level-only container kind.
_LEAF_KINDS = [
    "increment", "person_name", "person_email", "int_range",
    "decimal_range", "string_length", "values", "weighted", "pattern", "constant", "script",
]
_FIELD_KINDS = [*_LEAF_KINDS, "nested_list"]


@dataclass(frozen=True)
class NormalizeResult:
    """Result of _normalize(). Separates non-lossy repairs from unsupported features."""
    spec: dict[str, Any]
    notes: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


def _field_schema(kinds: list[str], allow_children: bool, allow_unique: bool = False) -> dict[str, Any]:
    """One field object. FLAT (no $ref): a local constrained-decoding runtime — Ollama's
    format=, llama.cpp's json-schema-to-GBNF — silently drops recursive $ref, so nesting is
    inlined to a fixed depth (top field -> optional leaf children) instead of self-referencing.

    `allow_unique` is deliberately only True for the top-level fields array: a shuffle
    sequence (see 'unique' below) is one stateful iterator shared across the whole
    generate statement, not reset per parent-record iteration, so it cannot express
    "unique within each nested item" — offering it inside nested_list's own leaf schema
    would let a model pick an option that silently produces wrong results. Not exposing
    it in the schema is the strongest form of that guard; _normalize()'s _field() also
    records an unsupported-feature error if a nested unique= is encountered anyway."""
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
    if allow_unique:
        props["unique"] = {
            "type": "boolean",
            "description": "int_range only: every generated value is distinct (no repeats "
            "across the whole field), drawn in a deterministic order. Size min/max to "
            "comfortably cover this field's generate count — if the range is smaller than "
            "the count, generation stops early (fewer rows), it does not repeat or error.",
        }
    if allow_children:
        # nested_list children are leaves only — one level of nesting, no recursion.
        props["fields"] = {"type": "array", "items": _field_schema(_LEAF_KINDS, allow_children=False)}
    return {"type": "object", "properties": props, "required": ["name", "kind"]}


def _passthrough_attrs(*names: str) -> dict[str, dict[str, Any]]:
    """Schema fragments for compact-spec properties that map 1:1 onto a GenerateModel field
    (same name, same meaning) — pulled from the model's own Field(description=/examples=) via
    reflection instead of hand-typed, so they can't drift from what the model actually says."""
    model_props = element_json_schema("generate")["properties"]
    out: dict[str, dict[str, Any]] = {}
    for name in names:
        prop = model_props.get(name, {})
        frag: dict[str, Any] = {"type": "string"}
        if "description" in prop:
            frag["description"] = prop["description"]
        if "examples" in prop:
            frag["examples"] = prop["examples"]
        out[name] = frag
    return out


def _generate_item_schema(allow_children: bool) -> dict[str, Any]:
    """One <generate> entry. `source`/`source_type` are a deliberate scaffold-level rename of
    the DSL's overloaded `type=` (a source-entity selector here, not a scalar cast — the exact
    ambiguity DM105 mis-handled) — hand-described, since this vocabulary doesn't map 1:1 onto the
    model. `start`/`end`/`interval` DO map 1:1, so their text comes from _passthrough_attrs."""
    props: dict[str, Any] = {
        "name": {"type": "string"},
        "count": {"type": "integer"},
        "target": {"type": "string", "description": "e.g. JSON, CSV, or a memstore id"},
        "fields": {
            "type": "array",
            "items": _field_schema(_FIELD_KINDS, allow_children=True, allow_unique=True),
        },
        "source": {
            "type": "string",
            "description": "Read all rows from a declared source (a memstore/database/mongodb id), "
            "one row per generated record, in order. Do not also set 'count' — the source supplies "
            "the row count. Reference a source column directly by its bare name in a field's "
            "script, e.g. kind='script', script='value * 2'.",
        },
        "source_type": {
            "type": "string",
            "description": "Which produced entity/table to read from 'source' when it holds more "
            "than one row-producer (a producer name, not a scalar type).",
        },
        **_passthrough_attrs("start", "end", "interval"),
    }
    if allow_children:
        props["children"] = {
            "type": "array",
            "items": _generate_item_schema(allow_children=False),
            "description": "Nested <generate> inside this one, e.g. a child list keyed to the "
            "parent (one level only).",
        }
    return {"type": "object", "properties": props, "required": ["name", "fields"]}


# JSON schema the model fills (pass as Ollama `format=` / structured output). No $ref.
SPEC_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "description": "Compact DATAMIMIC data-generation spec. See SPEC_PROMPT_GUIDE for the "
    "memstore-read-back and time-series patterns — they span multiple fields/attributes "
    "together, so no single field's description can teach the whole shape.",
    "properties": {
        "seed": {"type": "integer"},
        "generates": {"type": "array", "items": _generate_item_schema(allow_children=True)},
    },
    "required": ["generates"],
}

# A worked-example nudge for callers to embed in the PROMPT TEXT alongside
# format=SPEC_JSON_SCHEMA (not just attach to the schema object) — Ollama/llama.cpp's
# structured-output decoding constrains the grammar shape but does not inject
# description=/examples= strings into the model's own context, so a model that has never
# seen these multi-attribute patterns demonstrated will not discover them from field
# descriptions alone (confirmed: a stress test model fabricated fake field values instead
# of ever attempting source=/start= when given the schema with no prompt-side example; a
# later re-run confirmed it also invents a fake random.unique(min,max) function instead of
# the real unique= property when that pattern isn't demonstrated either).
SPEC_PROMPT_GUIDE = """Output exactly ONE generate per name — never multiple draft attempts \
under the same name, only the final one you want.

Three patterns the JSON schema alone won't teach you — copy their shape:

Memstore read-back (a later generate reads an earlier one's rows): set 'source' to the \
earlier generate's memstore target id, and 'source_type' to its 'name'. Reference a column \
by its BARE name in a field's script (never "producer.column").
{"generates": [
  {"name": "orders", "count": 20, "target": "mem,JSON",
   "fields": [{"name": "id", "kind": "increment"}, {"name": "amount", "kind": "int_range", "min": 1, "max": 100}]},
  {"name": "receipts", "target": "JSON", "source": "mem", "source_type": "orders",
   "fields": [{"name": "amount", "kind": "script", "script": "amount"},
              {"name": "doubled", "kind": "script", "script": "amount * 2"}]}
]}

Time series (readings over time instead of a plain count): set 'start', 'end', 'interval' \
together on the generate (never just one or two of them) — 'count' becomes the number of \
series, not the row count.
{"generates": [
  {"name": "readings", "count": 2, "target": "JSON",
   "start": "2025-01-01T00:00:00", "end": "2025-01-02T00:00:00", "interval": "PT1H",
   "fields": [{"name": "at", "kind": "script", "script": "ts.now"},
              {"name": "sensor", "kind": "script", "script": "ts.series"}]}
]}

Unique numeric values (e.g. seat numbers, no two records the same): set 'unique': true on an \
int_range FIELD (not on the generate) — do not invent a script function for this, the \
property already exists. Size min/max to comfortably cover the field's count.
{"generates": [
  {"name": "passengers", "count": 150, "target": "JSON",
   "fields": [{"name": "seat_number", "kind": "int_range", "min": 1, "max": 180, "unique": true}]}
]}
"""

_ENTITY_VAR = "_ent_person"  # single shared Person variable when person_* fields appear

# Local constrained-decoding runtimes (Ollama format=) don't strictly enforce the schema —
# models emit near-miss keys. Normalize the common drift so a semantically-correct spec renders.
_KIND_ALIASES = {
    "id": "increment", "auto": "increment", "sequence": "increment", "autoincrement": "increment",
    "name": "person_name", "fullname": "person_name", "full_name": "person_name", "person": "person_name",
    "email": "person_email",
    "int": "int_range", "integer": "int_range", "number": "int_range", "number_range": "int_range",
    "float": "decimal_range", "decimal": "decimal_range", "money": "decimal_range",
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


def _dedupe_by_name(gens: list[dict[str, Any]], notes: list[str]) -> list[dict[str, Any]]:
    """Last-entry-wins de-duplication by name. Observed: a model emitting several draft
    attempts under the SAME generate name in one response (an incomplete early draft
    followed by a corrected one) — DM403 would otherwise reject the whole descriptor even
    when the last draft is the correct one. Keeps each name's LAST entry, at its
    first-seen position. Every dropped earlier draft emits a note — nothing is dropped
    silently, per the normalization-diagnostics contract."""
    order: list[str] = []
    by_name: dict[str, dict[str, Any]] = {}
    dropped: dict[str, int] = {}
    for gen in gens:
        name = gen["name"]
        if name not in by_name:
            order.append(name)
        else:
            dropped[name] = dropped.get(name, 0) + 1
        by_name[name] = gen
    for name, count in dropped.items():
        notes.append(
            f"generate '{name}': {count} earlier draft(s) with the same name dropped, "
            "keeping the last"
        )
    return [by_name[name] for name in order]


def _normalize(spec: dict[str, Any]) -> NormalizeResult:
    """Map a model's near-miss JSON onto the canonical spec shape (generate->generates,
    weighted_values->weighted, 'x.json' target->JSON, kind/type & name/field aliases).
    Returns NormalizeResult with the normalized spec and any diagnostics (notes for
    non-lossy repairs, errors for unsupported features)."""
    gens = spec.get("generates") or spec.get("generate") or spec.get("entities") or []
    if isinstance(gens, dict):
        gens = [gens]

    notes: list[str] = []
    errors: list[str] = []

    def _field(f: dict[str, Any], top_level: bool = True, field_name_hint: str = "") -> dict[str, Any]:
        out = dict(f)
        out["name"] = f.get("name") or f.get("field") or f.get("column") or "field"
        field_display = out["name"] or field_name_hint
        raw_kind = str(f.get("kind") or f.get("type") or "constant").strip().lower()
        out["kind"] = _norm_kind(f.get("kind") or f.get("type"))
        # Note: kind alias applied (e.g. weighted_values→weighted, id→increment)
        if raw_kind in _KIND_ALIASES and raw_kind != out["kind"]:
            notes.append(f"kind '{raw_kind}' normalized to '{out['kind']}'")

        # Near-miss: "constant" chosen but a values list was given instead of a scalar
        # value -> the model meant "values" (observed: kind="constant", values=[...]).
        if out["kind"] == "constant" and f.get("values") and not f.get("value"):
            out["kind"] = "values"
            notes.append("constant with values list corrected to kind='values'")

        # Near-miss: "values"/"weighted" chosen but only a scalar value was given (e.g. a
        # slash- or comma-joined string) -> split it into a values list (observed:
        # kind="weighted", value="pizza/pasta/salad/soup", weights=[2,1,1,1]).
        if out["kind"] in ("values", "weighted") and not f.get("values") and f.get("value"):
            raw = str(f["value"])
            sep = "/" if "/" in raw else ("," if "," in raw else None)
            if sep:
                out["values"] = [v.strip() for v in raw.split(sep) if v.strip()]
                notes.append(f"{out['kind']} field '{field_display}' split scalar value into values list")

        # Near-miss: same as above, but the model put a Python-list-literal STRING in
        # script= instead of value= (observed: kind="weighted", script="['pasta',
        # 'pizza', 'salad/soup']"). Parsed, not just split, since it's already valid
        # Python list syntax.
        if out["kind"] in ("values", "weighted") and not f.get("values") and f.get("script"):
            script_val = str(f["script"]).strip()
            if script_val.startswith("[") and script_val.endswith("]"):
                try:
                    parsed = ast.literal_eval(script_val)
                except (ValueError, SyntaxError):
                    parsed = None
                if isinstance(parsed, list):
                    out["values"] = [str(v) for v in parsed]
                    notes.append(f"{out['kind']} field '{field_display}' converted script list literal to values array")

        # Near-miss: the model signaled uniqueness in its own words instead of
        # discovering the unique= property — either as a hint alongside a correctly-
        # chosen int_range kind (observed: kind="int_range", script="unique_per_flight"),
        # or as a full fake-function fallback when it picked kind="script" instead of
        # int_range entirely (observed: kind="script", script="random.unique(1, 180)").
        # Only ever inferred, never overrides an explicit unique= the spec already set
        # (True or False) — checked via key presence, not truthiness, for that reason.
        script_text = str(f.get("script") or "")
        if "unique" not in f:
            if out["kind"] == "int_range" and script_text.strip().lower().startswith("unique"):
                out["unique"] = True
                if top_level:
                    notes.append(
                        f"int_range field '{field_display}' with 'unique' script hint converted to unique=true"
                    )
            else:
                range_match = _UNIQUE_RANGE_SCRIPT_RE.search(script_text)
                if range_match:
                    out["kind"] = "int_range"
                    out["min"] = int(range_match.group(1))
                    out["max"] = int(range_match.group(2))
                    out["unique"] = True
                    if top_level:
                        notes.append(
                            f"script field '{field_display}' with 'random.unique(...)' function "
                            f"converted to int_range unique=true"
                        )

        if not top_level:
            # unique= is top-level-only: a shuffle sequence is one stateful iterator
            # shared across the whole statement, not reset per parent-record iteration,
            # so applying it inside a nested_list would silently under-produce instead of
            # being per-parent-unique. Record an unsupported-feature error and remove it.
            if out.get("unique"):
                errors.append(
                    f"unsupported feature: unique=true inside a nested list (field '{field_display}') "
                    f"— per-parent uniqueness is not supported by the scaffold renderer; restructure with "
                    f"a top-level generate (e.g. passengers as their own generate joined to flights via "
                    f"source=) or author raw XML"
                )
            out.pop("unique", None)

        children = f.get("fields") or f.get("children")
        if children:
            out["kind"] = "nested_list"
            out["fields"] = [
                _field(c, top_level=False, field_name_hint=field_display)
                for c in children if isinstance(c, dict)
            ]
        return out

    def _generate(gen: dict[str, Any], allow_children: bool) -> dict[str, Any]:
        fields = gen.get("fields") or gen.get("keys") or gen.get("columns") or []
        gen_name: str = str(gen.get("name") or "data")
        out = {
            "name": gen_name,
            "count": gen.get("count"),
            "target": _norm_target(gen.get("target")),
            "fields": [_field(f, field_name_hint=gen.get("name") or "data") for f in fields if isinstance(f, dict)],
            "source": gen.get("source"),
            "source_type": gen.get("source_type") or gen.get("type"),
            "start": gen.get("start"),
            "end": gen.get("end"),
            "interval": gen.get("interval"),
        }
        if allow_children:
            # One level only — matches _field_schema's existing anti-recursion discipline.
            children = gen.get("children") or gen.get("nested") or []
            child_gens = []
            for c in children:
                if isinstance(c, dict):
                    child_name = c.get("name") or "child"
                    # Check for grandchildren (third hierarchy level) — not allowed.
                    grandchildren = c.get("children") or c.get("nested") or []
                    if grandchildren:
                        for gc in grandchildren:
                            if isinstance(gc, dict):
                                gc_name = gc.get("name") or "grandchild"
                                errors.append(
                                    f"unsupported feature: generate '{gc_name}' nested more than one level deep "
                                    f"(inside '{child_name}' which is inside '{gen_name}') — the scaffold spec "
                                    f"supports one level of nesting; flatten deeper levels into their own "
                                    f"top-level generates joined via source=/memstore, or author raw XML"
                                )
                    child_gens.append(_generate(c, allow_children=False))
            out["children"] = _dedupe_by_name(child_gens, notes)
        return out

    norm_gens = _dedupe_by_name(
        [_generate(gen, allow_children=True) for gen in gens if isinstance(gen, dict)], notes
    )
    return NormalizeResult(
        spec={"seed": spec.get("seed"), "generates": norm_gens},
        notes=tuple(notes),
        errors=tuple(errors),
    )


def _quote_values(values: list[str]) -> str:
    return ", ".join("'" + str(v).replace("'", "\\'") + "'" for v in values)


def _render_field(
    field: dict[str, Any], indent: str, entity_var: str = _ENTITY_VAR, depth: int = 0
) -> list[str]:
    name = field["name"]
    kind = field.get("kind", "constant")
    a = f'name={quoteattr(name)}'
    if kind == "increment":
        return [f'{indent}<key {a} generator="IncrementGenerator"/>']
    if kind == "person_name":
        return [f'{indent}<key {a} script="{entity_var}.name"/>']
    if kind == "person_email":
        return [f'{indent}<key {a} script="{entity_var}.email"/>']
    if kind == "int_range":
        lo, hi = int(field.get("min", 0)), int(field.get("max", 100))
        if field.get("unique"):
            # CE's real unique-numeric-range mechanism (confirmed against
            # test_sequence_distributions.py): a deterministic strided walk over the
            # range grid, each value exactly once, until exhausted. unique= never
            # combines with a bare int range at the model-validation layer.
            return [f'{indent}<key {a} type="int" min="{lo}" max="{hi}" distribution="shuffle"/>']
        return [f'{indent}<key {a} type="int" min="{lo}" max="{hi}"/>']
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
        sub_fields = field.get("fields", [])
        inner = indent + "    "
        nested_depth = depth + 1
        nested_entity_var = _entity_var_name(nested_depth)
        lines = [f'{indent}<nestedKey {a} type="list" minCount="{lo}" maxCount="{hi}">']
        if _uses_person(sub_fields):
            # A DISTINCT name per nesting depth, not the outer entity_var: the engine
            # resolves a bare script name against the NEAREST ancestor scope that
            # declares it, so reusing the outer name here would make every item read the
            # same one shared Person again (the exact bug this exists to fix — see
            # _entity_var_name).
            lines.append(f'{inner}<variable name="{nested_entity_var}" entity="Person"/>')
        for sub in sub_fields:
            lines += _render_field(sub, inner, nested_entity_var, nested_depth)
        lines.append(f"{indent}</nestedKey>")
        return lines
    # unknown kind -> a safe constant so structure stays valid
    return [f'{indent}<key {a} constant={quoteattr(str(field.get("value", "")))}/>']


def _uses_person(fields: list[dict[str, Any]]) -> bool:
    """Non-recursive by design: each scope (an outer generate, a child generate, a
    nested_list) decides for ITSELF whether it needs its own Person variable, based only
    on its own direct fields — never by looking through a nested scope's fields, which
    would make an outer scope declare an unused variable just because something nested
    inside it happens to need a person (and that nested thing gets its own, per
    _entity_var_name)."""
    return any(f.get("kind", "").startswith("person_") for f in fields)


def _entity_var_name(depth: int) -> str:
    """A DISTINCT Person-variable name per nesting depth. Required, not cosmetic: the
    engine resolves a bare script name against the nearest ancestor scope that declares
    it (test-proven: a nested scope's own same-named variable is shadowed by an
    ancestor's), so two different depths reusing one name would silently collapse back
    into the single-shared-person bug this naming scheme exists to prevent. Sibling
    scopes at the same depth (e.g. a generate's own nested_list field and its child
    generate) safely share a name — they are never in an ancestor/descendant
    relationship with each other, so there is nothing to shadow between them."""
    return _ENTITY_VAR if depth == 0 else f"{_ENTITY_VAR}_{depth}"


def _check_unique_fits(fields: list[dict[str, Any]], count: Any) -> None:
    """Guard against unique=True on an int_range field whose grid is smaller than the
    generate's count: distribution="shuffle" (see _render_field) stops early rather than
    erroring, silently producing fewer rows — exactly the kind of trap this renderer
    exists to remove, so it's raised here instead of discovered downstream."""
    if count is None:
        return
    for f in fields:
        if not f.get("unique") or f.get("kind") != "int_range":
            continue
        lo, hi = int(f.get("min", 0)), int(f.get("max", 100))
        grid = hi - lo + 1
        if grid < int(count):
            raise ValueError(
                f"field '{f.get('name')}': unique=true over [{lo}, {hi}] has only {grid} "
                f"possible values, but the generate needs {count} rows — widen the range "
                "or drop unique"
            )


def _iter_generates(gens: list[dict[str, Any]]):
    """Depth-first over a generate and its (one level of) children — used so memstore
    auto-declaration and rendering both see nested generates, not just top-level ones."""
    for gen in gens:
        yield gen
        yield from _iter_generates(gen.get("children", []))


def _render_generate(gen: dict[str, Any], indent: str, depth: int = 0) -> list[str]:
    fields = gen.get("fields", [])
    _check_unique_fits(fields, gen.get("count"))
    inner = indent + "    "
    entity_var = _entity_var_name(depth)
    attrs = f'name={quoteattr(gen["name"])}'
    if gen.get("source"):
        # Source-backed: the source supplies the row count. Deliberately never emit 'count'
        # here even if the spec set one — two numbers (writer's count, reader's count) that
        # must stay in sync is exactly the kind of trap this renderer exists to remove.
        attrs += f' source={quoteattr(gen["source"])}'
        if gen.get("source_type"):
            attrs += f' type={quoteattr(gen["source_type"])}'
        attrs += ' distribution="ordered"'
    elif gen.get("count") is not None:
        attrs += f' count="{int(gen["count"])}"'
    if gen.get("target"):
        attrs += f' target={quoteattr(gen["target"])}'
    for attr in ("start", "end", "interval"):
        if gen.get(attr):
            attrs += f' {attr}={quoteattr(str(gen[attr]))}'
    lines = [f"{indent}<generate {attrs}>"]
    if _uses_person(fields):
        lines.append(f'{inner}<variable name="{entity_var}" entity="Person"/>')
    for field in fields:
        lines += _render_field(field, inner, entity_var, depth)
    for child in gen.get("children", []):
        lines += _render_generate(child, inner, depth + 1)
    lines.append(f"{indent}</generate>")
    return lines


def _target_exempt_names() -> set[str]:
    """Target keywords that are NOT a memstore id — the same registries reference.py's
    targets_reference() derives from, not a hand-typed duplicate. A prior hand-typed copy of
    this set silently missed a real exporter ('FixedWidth'), which is exactly the drift a
    reflected set can't have."""
    from datamimic_ce.constants.exporter_constants import EXPORTER_CONSOLE_EXPORTER, EXPORTER_LOG_EXPORTER
    from datamimic_ce.exporters.exporter_util import _BUFFERED_EXPORTERS

    return set(_BUFFERED_EXPORTERS) | {EXPORTER_CONSOLE_EXPORTER, EXPORTER_LOG_EXPORTER}


def _render_normalized(canonical_spec: dict[str, Any]) -> str:
    """Render an already-normalized spec dict into a structurally-valid DATAMIMIC descriptor
    string. Called after _normalize() has validated the spec structure. Raises ValueError
    only for structural/logical errors like unsupported configurations, never silently
    emitting a wrong descriptor."""
    generates = canonical_spec["generates"]
    if not generates or not any(g["fields"] for g in generates):
        raise ValueError(
            "spec needs a non-empty 'generates' list with fields, e.g. "
            "{'generates': [{'name': 'x', 'count': 10, 'fields': [{'name': 'id', 'kind': 'increment'}]}]}"
        )

    seed = canonical_spec.get("seed")
    setup_open = f'<setup rngSeed="{int(seed)}">' if seed is not None else "<setup>"
    lines = [setup_open]

    # Declare any memstore referenced as a target (top-level or nested) so DM402 stays clean.
    memstore_ids = {
        t.strip()
        for g in _iter_generates(canonical_spec.get("generates", []))
        for t in str(g.get("target", "")).split(",")
        if t.strip() and t.strip() not in _target_exempt_names()
    }
    for mid in sorted(memstore_ids):
        lines.append(f'    <memstore id={quoteattr(mid)}/>')

    for gen in canonical_spec.get("generates", []):
        lines += _render_generate(gen, "    ")

    lines.append("</setup>")
    return "\n".join(lines)


def render(spec: dict[str, Any]) -> str:
    """Render a spec dict into a structurally-valid DATAMIMIC descriptor string.

    Tolerant of a model's near-miss key drift (see _normalize). Raises ValueError with
    a clear message if there are unsupported features or structural errors — never
    silently emits a wrong descriptor.
    """
    result = _normalize(spec)
    if result.errors:
        raise ValueError("; ".join(result.errors))
    return _render_normalized(result.spec)


@dataclass
class ScaffoldCheckResult:
    """Result of check(). `stage` names WHICH check() PHASE this result reflects
    ("render"/"lint"/"dry_run") — a different concept from DryRunResult's own internal
    `.stage` ("lint"/"run", exposed via `dryrun_result.stage`), which reflects where
    dry_run_source's own re-lint-then-run sequence stopped. Don't conflate the two."""

    ok: bool
    stage: str  # "render" | "lint" | "dry_run"
    xml: str | None
    render_error: str | None = None
    normalization_notes: tuple[str, ...] = ()
    lint_result: Any = None  # LintResult, set once past the render stage
    dryrun_result: Any = None  # DryRunResult, set only when stage == "dry_run"


def check(
    spec: dict[str, Any],
    *,
    dry_run: bool = True,
    max_count: int = 10,
    sample_rows: int = 5,
) -> ScaffoldCheckResult:
    """_normalize() -> _render_normalized() -> lint_source() -> optionally dry_run_source(),
    stopping at the first failing stage. The one pipeline the MCP `datamimic_scaffold` tool
    and the CLI `datamimic scaffold` command both call and then format for their own
    transport — extracted after two independently-written copies of this sequencing drifted
    (different stage values for the same phase, inconsistent error shapes). Normalizes once,
    surfaces any diagnostics."""
    from datamimic_ce.authoring.dryrun import dry_run_source
    from datamimic_ce.authoring.linter import lint_source

    norm_result = _normalize(spec)
    norm_notes = norm_result.notes

    if norm_result.errors:
        return ScaffoldCheckResult(
            ok=False, stage="render", xml=None, render_error="; ".join(norm_result.errors),
            normalization_notes=norm_notes,
        )

    try:
        xml = _render_normalized(norm_result.spec)
    except ValueError as err:
        return ScaffoldCheckResult(
            ok=False, stage="render", xml=None, render_error=str(err),
            normalization_notes=norm_notes,
        )

    lint_result = lint_source(xml)
    if not lint_result.ok:
        return ScaffoldCheckResult(
            ok=False, stage="lint", xml=xml, lint_result=lint_result,
            normalization_notes=norm_notes,
        )

    if not dry_run:
        return ScaffoldCheckResult(
            ok=True, stage="lint", xml=xml, lint_result=lint_result,
            normalization_notes=norm_notes,
        )

    dryrun_result = dry_run_source(xml, max_count=max_count, sample_rows=sample_rows)
    return ScaffoldCheckResult(
        ok=dryrun_result.ok,
        stage="dry_run",
        xml=xml,
        lint_result=lint_result,
        dryrun_result=dryrun_result,
        normalization_notes=norm_notes,
    )
