# CE → EE parity gap: implementation brief

**Audience:** an EE implementation agent/engineer working in `datamimic-ee`.
**Produced from:** `datamimic` (CE) source investigation on 2026-07-13 — every field
name, validator rule, and file path below was read directly from CE's code, not
inferred.
**Approach:** TDD. Each item below lists CE's exact behavior as the spec, and a
CE test suite to port/adapt as the first thing to write in EE, before any
implementation code.

## Why this exists

CE and EE are separate repos with no import relationship in either direction (CE is
public on PyPI, EE is not). CE's Pydantic models are the single source of truth for
what CE's DSL accepts; this document is the one-directional bridge — it specifies,
in EE's own terms, the CE surface EE does not yet support, so EE can decide to either
close each gap or explicitly scope around it. Do not treat this as a request to make
EE import or wrap CE code — every item is a from-scratch EE implementation, written
in EE's own architectural style, verified independently against the acceptance
criteria below (not against CE's runtime).

## Scope

Two kinds of gap, found by diffing CE's `ELEMENT_MODEL_MAP` (`datamimic_ce/authoring/schema.py`)
against EE's `element_registry.py` element/field registries:

1. **Structural** — 3 DSL elements that exist in CE and are entirely absent from EE:
   `<demographics>`, `<state-machine>` (+ child `<transition>`), `<while>`.
2. **Field-level** — 6 attributes on elements EE otherwise already supports, where
   EE's equivalent Pydantic model is missing the attribute: `<generate>`/`<iterate>`
   (`minCount`, `maxCount`, `multiprocessing`, `offset`), `<nestedKey>` (`sourceEntity`),
   `<variable>` (`weights`).

This is exhaustive for element/attribute-level gaps as of the date above — every
other CE element and every other attribute on a shared element has a matching EE
field. (EE has many elements/attributes CE lacks — `ama-generate`, `kafka-*`,
`ml-train`, `stratifyBy`, `samplingTemperature`, etc. That is not in scope here;
EE being a superset elsewhere is expected and not a gap.)

**Caveat — this proves presence parity, not behavioral parity.** The diff this
brief is built from compares field *names* (aliases), not validation rules or
runtime semantics. A field that exists on both sides but validates or behaves
differently in EE would still break a CE script and would not show up in this
diff. Closing all 8 items below is necessary for "EE runs all CE scripts" but is
not by itself sufficient — treat the acceptance-criteria test lists per item as
the actual behavioral contract to match, not the mere existence of the field.

## Architecture guidance — match EE's own conventions, not CE's

- **Pydantic model style**: EE already documents fields via
  `Field(description=..., examples=[...], json_schema_extra={"detail": ...})` (see
  `datamimic_ee/model/generate_model.py`'s existing fields for the house style — 46/46
  fields already follow it). Every new field below should be added in that same style,
  not CE's plainer `Field(description=..., examples=[...])` form.
- **Registry wiring**: EE dispatches elements through `datamimic_ee/model/element_registry.py`'s
  `_ELEMENT_CHILDREN` (nesting table) and `_get_element_parsers()` (tag → parser).
  `<demographics>` and `<state-machine>`+`<transition>` need new entries there, matching
  the pattern of an existing setup-level, singleton element already in EE's registry
  (structurally closest existing thing: `<memstore>` — also setup-scoped, single
  registration, referenced by id later).
- **JSON schema / autocomplete surface**: once new models exist, EE's `element_metadata_util.py`
  reflects them into the autocomplete schema automatically via `model_json_schema()` —
  no separate manual schema update needed, that's the whole point of EE's existing
  reflection-based design (mirrored this session on the CE side too, see
  `datamimic_ce/authoring/schema.py`'s `element_json_schema()`).
- **Do not add EE-only extras while porting.** Port CE's fields as CE defines them.
  If EE's product needs additional attributes on top (e.g. EE-specific demographic
  config), that's separate follow-up work, not part of closing this gap.

## Gap inventory

| # | Element/attribute | Kind | CE model file | Complexity |
|---|---|---|---|---|
| 1 | `<while>` | structural | `datamimic_ce/model/while_model.py` | Low — self-contained, no cross-subsystem dependency |
| 2 | `<generate>`/`<iterate>` `offset` | field | `datamimic_ce/model/generate_model.py` | Low — well isolated, most thoroughly tested item in this brief |
| 3 | `<generate>`/`<iterate>` `minCount`/`maxCount` | field | `datamimic_ce/model/generate_model.py` | Low-medium — shared validator, touches count-resolution |
| 4 | `<nestedKey>` `sourceEntity` | field | `datamimic_ce/model/nested_key_model.py` | Low-medium — only meaningful for memstore sources |
| 5 | `<variable>` `weights` | field | `datamimic_ce/model/variable_model.py` | Low-medium — CE has zero direct test coverage; build from `<key>`'s equivalent |
| 6 | `<generate>`/`<iterate>` `multiprocessing` | field | `datamimic_ce/model/generate_model.py` | **Design decision required before implementing — see item 6** |
| 7 | `<state-machine>` + `<transition>` | structural | `datamimic_ce/model/state_machine_model.py` | Medium — new stateful generator subsystem |
| 8 | `<demographics>` | structural | `datamimic_ce/model/demographics_model.py` | High — touches entity-generator subsystem broadly |

Recommended implementation order: 1 → 2 → 3 → 4 → 5, resolve the item-6 design
question, then 6 → 7 → 8 (ascending complexity; each item is independently
shippable, no ordering dependency between them except developer familiarity).

---

## 1. `<while>`

**CE spec** (`while_model.py`, `while_parser.py`, `datamimic_ce/statements/while_statement.py`,
`datamimic_ce/tasks/while_task.py`):

- Fields: `condition: str` (required, non-empty — raises on `""`), `max_iterations: int`
  (XML attr `maxIterations`, default `10000`).
- Legal wherever a `<generate>`/`<nestedKey>` body is legal (including inside
  `<condition>`/`<if>` and nested `<while>` bodies) — it has no fixed child set,
  it inherits whatever its enclosing composite statement accepts.
- Runtime: `condition` is a **raw Python boolean expression**, evaluated fresh
  before every iteration against the current row's context (same expression
  language as `script=`/other `condition=` attributes elsewhere in the DSL — not a
  separate mini-language). Loop body = every child element, executed in document
  order, once per iteration, mutating the current row's fields/variables (nothing
  is auto-accumulated into a list — it's a per-row side-effect loop, not a
  collection iterator).
- **Hard failure, not silent stop**: if the condition is still true after
  `max_iterations` iterations, raise (CE's message: `"<while> exceeded
  max_iterations={max_iterations}: condition '{condition}' never became false
  (possible infinite loop)"`). This must be a real, catchable error in the EE
  port too — a silently-capped loop would hide an actual authoring bug.
- Loop state does not leak across rows: `<generate count="N">` re-runs the whole
  row body per row, so each row's `<while>` execution starts fresh (this is a
  natural consequence of correct per-row scoping, not special `<while>` logic —
  verify it holds in the EE port anyway, it's exactly the kind of thing that's
  easy to accidentally get wrong with shared/cached state).

**TDD test list to port (from `tests_ce/integration_tests/test_while/test_while.py`,
5 scenarios — port as EE's first while-loop test file):**

1. Loop runs until `condition` goes false, correct final value; running it
   `count="3"` times (independent rows) gives every row the same independently-computed
   final value — proves no state leaks between rows.
2. `maxIterations` exceeded on a genuinely infinite condition (`condition="True"`) →
   raises, error message names `max_iterations`.
3. Missing `condition` attribute → raises (Pydantic required-field error).
4. Empty `condition=""` → raises, error message names the emptiness.
5. A realistic "loop until a computed predicate holds" case (CE's example: read a
   value from a source, increment it until it passes a checksum function defined via
   an inline-script element) — proves the condition can call a helper function
   defined elsewhere in the same descriptor's scope, not just reference bare fields.

---

## 2. `<generate>`/`<iterate>` — `offset`

**CE spec** (`generate_model.py` lines ~83-90, `datamimic_ce/data_sources/data_source_registry.py`,
`datamimic_ce/tasks/task_util.py`):

- Field: `offset: int | None`, `ge=0` (negative rejected at the Pydantic layer).
- Validator: requires `source` to also be set (`"'offset' requires a 'source' - it
  skips the first N source rows"`).
- **File sources only.** Explicitly rejected for a memstore source
  (`"offset= is only supported for file sources, not memstore '<id>'"`) and for a
  database/mongodb client source (`"... not database client '<id>' - use a
  selector with an SQL/Mongo skip instead"`).
- Runtime: skip is applied to the raw row list **before** any pagination window or
  cyclic wrap — so a default `count` (when `count` is omitted) shrinks to the
  post-offset remainder, cyclic wrap only ever cycles the post-offset rows (never
  re-includes skipped ones), and multi-worker chunked reads all shift by the same
  offset consistently (no duplicate/dropped rows at chunk seams).

**TDD test list to port (from `tests_ce/integration_tests/test_iterate_offset/test_iterate_offset.py`
— 12 scenarios, the most thoroughly tested item in this brief; port near-verbatim):**

1. Offset skips N rows and default count shrinks to the remainder.
2. Cyclic wrap only cycles the post-offset region.
3. Paginated reads stay aligned across pages.
4. Random-distribution pool excludes skipped rows.
5. Multi-worker chunked reads stay aligned (no dupes/gaps at chunk seams) — both
   plain and cyclic.
6. Multi-worker random distribution is duplicate-free over the post-offset remainder.
7. Offset beyond the source length yields zero rows (not an error).
8. Missing `source` → raises.
9. Negative offset → raises.
10. Every supported file format (CSV/JSON/XML/fixed-width/XLSX) honors offset identically.
11. Memstore source + offset → raises, naming "file sources" in the message.
12. Database/mongodb client source + offset → raises, naming "file sources" in the message.

---

## 3. `<generate>`/`<iterate>` — `minCount` / `maxCount`

**CE spec** (`generate_model.py`, `model_util.py`'s `check_min_max_count`,
`statement_util.py`'s `resolve_count`, `generate_task.py`, `nested_key_task.py`):

- Fields: `min_count: int | None` (XML `minCount`), `max_count: int | None`
  (XML `maxCount`). Same pair, same validator, shared between `<generate>` and
  `<nestedKey>` in CE — **implement identically on both elements in EE.**
- Validator rules: mutually exclusive with `count` (all three together → raises,
  naming the element tag). If both present, `minCount <= maxCount` required
  (equal is fine, only `>` rejected). Either alone (without the other, without
  `count`) is legal and satisfies the "some row-count source is required" rule.
  In time-series mode (`start`/`end`/`interval` all set — see CE's
  `datamimic_ce/authoring/reference_data/cheatsheet.md` for that feature if EE
  doesn't have an equivalent), this pair becomes fully optional.
- Runtime: when both are set, actual count = `random.randint(min_count, max_count)`
  (inclusive, uniform), rolled once per statement execution, drawn from the
  same seeded RNG the rest of the run uses (so it's reproducible under a fixed
  seed). Only `max_count` set → a 5-wide window below max. Only `min_count` set →
  a 5-wide window above min. (Confirm EE wants this exact 5-wide-window behavior
  for the single-bound case, or wants to require both bounds together — CE's choice
  here is somewhat arbitrary and worth an explicit EE decision, not a blind port.)

**TDD test list to port (from `tests_ce/integration_tests/test_generate_count_range/`):**

1. Row count falls within `[minCount, maxCount]` and is identical across two runs
   with the same seed.
2. `count` + `minCount`/`maxCount` together → raises.
3. Nested `<generate>` inside a parent: each parent instance independently rolls
   its own child count in range (totals validated against `parents × [min,max]`),
   reproducible under seed.
4. `minCount`/`maxCount` combined with a `source=` pool: picked count within range,
   values genuinely come from the source pool, deterministic under seed + ordered
   distribution.

**CE gap worth closing in the EE port, not just porting the gap forward**: CE has no
isolated Pydantic-level unit test for this validator (`check_min_max_count`) — only
full-pipeline integration coverage. Add a direct model-level unit test in EE as part
of this work (fast, no data-generation pipeline needed to exercise a validator).

---

## 4. `<nestedKey>` — `sourceEntity`

**CE spec** (`nested_key_model.py`, `datamimic_ce/statements/statement_util.py`'s
`resolve_source_entity`, `nested_key_task.py`):

- Field: `source_entity: str | None` (XML `sourceEntity`). No dedicated validator
  requiring `source` to also be set (unlike `offset`) — it's legal but inert without
  a `source`.
- **Only has a runtime effect when `source` points at a `<memstore>` id.** For file
  sources (`.csv`/`.json`/etc.), CE's file-format read branches ignore
  `sourceEntity`/`type` entirely and read the whole file directly.
- Runtime: resolves via the shared precedence chain used identically for
  `<generate>`/`<iterate>`/`<variable>`/`<nestedKey>`: `sourceEntity → type → name`
  (`StatementUtil.resolve_source_entity`) — implement this as one shared helper in
  EE if it doesn't already exist there in some form, not four separate
  copy-pasted resolution branches. It picks which producing statement's rows
  (by entity/type/name) to pull back out of the named memstore, overriding the
  default `type`-then-`name` fallback.
- **A known CE-internal asymmetry, worth deciding on rather than blindly porting**:
  `GenerateModel.source_entity`/`target_entity` have a blank/path-traversal guard
  validator (`_entity_not_blank`: strips, rejects empty, rejects `/`, `\`, `..`);
  `NestedKeyModel.source_entity` does not have the equivalent guard in CE today.
  Recommend EE add the guard uniformly to all four `sourceEntity`/`targetEntity`-family
  fields rather than reproducing CE's inconsistency.

**TDD test list to port (from `tests_ce/integration_tests/test_entity_matrix/test_entity_matrix.py`):**

1. A memstore seeded under one producer name; a `<nestedKey source="mem"
   sourceEntity="<name>">` reads exactly that producer's rows back, each parent
   record getting its own child rows correctly.
2. Contrast case: a **file** source's `type=` attribute is a pure structure marker
   (list vs. dict), not a `sourceEntity`-style routing hint — assert file-source
   behavior is unaffected by `sourceEntity` being present or absent.
3. Unit test of the shared `sourceEntity → type → name` precedence resolver in
   isolation (not tied to `<nestedKey>` specifically, since it's shared logic).

---

## 5. `<variable>` — `weights`

**CE spec** (`variable_model.py`, `model_util.py`'s `check_weights_require_values` /
`check_unique_constraints`, the shared `key_variable_task.py` used by both
`<key>` and `<variable>`):

- Field: `weights: str | None` — comma-separated relative weights, one per `values`
  entry (e.g. `"0.7,0.2,0.1"`). Type is a raw string at the model layer; parsed at
  runtime (`ast.literal_eval`), not a typed list.
- Validators: requires `values` also present (`"'weights' is only allowed together
  with 'values'"`). Mutually exclusive with `unique` (`"'unique' cannot be combined
  with 'weights'"` — no weighted sampling without replacement).
- **Length-match check (weights count == values count) happens at runtime, not at
  the model/validation layer** in CE — decide whether EE wants to move this earlier
  (a Pydantic `model_validator` catching it at construction) rather than reproducing
  CE's deferred-to-runtime placement; either is defensible, but make it a deliberate
  choice.
- Runtime: weights need not sum to 1 (normalized by the weighted-choice draw);
  drawn via a seeded RNG so it's reproducible under a fixed seed; **with**
  replacement (a `<variable>` with `weights` set still draws independently each
  record, unlike `unique`).

**TDD test list — CE has zero direct test coverage of `weights` on `<variable>`
specifically (confirmed: no XML fixture, no model unit test).** The nearest CE
analog is `<key>`'s `weights` (identical validators, identical runtime path) —
**mirror this suite from `tests_ce/integration_tests/test_weighted_values/test_weighted_values.py`
onto `<variable>`, one-for-one, as EE's actual test spec:**

1. Observed pick proportions approximate the declared weights within tolerance;
   identical results across two runs with the same seed.
2. `None` is a valid value among the weighted choices, works like any other.
3. `weights` length mismatched against `values` length → raises.
4. `weights` present without `values` → raises.
5. `unique=True` combined with `weights` → raises (currently untested anywhere in
   CE, on either `<key>` or `<variable>` — add it as new coverage in EE, don't skip
   it just because CE never wrote it).

---

## 6. `<generate>`/`<iterate>` — `multiprocessing` — **design decision required**

**CE spec, with an important caveat:** the field exists
(`multiprocessing: bool | None`, no alias) and is stored on the statement, but in
CE's current (Ray-refactored) execution path, **`GenerateTask._determine_num_workers`
never reads it** — actual worker-count decisions come entirely from `numProcess`
(a separate attribute) and `<setup rngSeed>`-forces-single-process /
unique-forces-single-process / delete-target-forces-single-process rules, none of
which consult the `multiprocessing` boolean. Every CE unit test that asserts
"multiprocessing=True/False changes execution path" is currently
`@pytest.mark.skip("Need rework with ray")`.

**Decide before implementing, don't silently replicate either behavior**:

- **(a) Faithful port**: add the field, parse/store it, document it, but don't wire
  it into worker-count decisions — matches CE's current (arguably accidental)
  behavior exactly.
- **(b) Fix-forward port**: use this as the opportunity to make
  `<generate multiprocessing="false">` actually force single-process for that
  statement regardless of `numProcess`/context defaults — arguably the behavior a
  user would expect from the attribute's name, and the skipped CE tests describe
  exactly this as the intended semantics.

The skipped tests in `tests_ce/unit_tests/test_task/test_generate_task.py`
(`test_execute_single_process`, `test_execute_multiprocess`,
`test_multiprocessing_decision` — a 4-case parametrized test: explicit
multiprocessing, default-to-context-setting, MongoDB-delete-forces-single,
explicitly-disabled) are the closest thing to a spec for option (b); resurrect and
adapt them as EE's TDD test list if (b) is chosen. If (a) is chosen, a single test
asserting the field parses/round-trips and has no observable effect on worker count
is sufficient.

---

## 7. `<state-machine>` + `<transition>`

**CE spec** (`state_machine_model.py`, `state_machine_parser.py`,
`datamimic_ce/statements/state_machine_statement.py`, `state_machine_task.py`,
`datamimic_ce/domains/common/literal_generators/state_transition_generator.py`):

- `<state-machine id="..." start="...">` — `id` required non-empty (this becomes
  the name later referenced as `generator="<id>"`); `start` optional, defaults to
  the first `<transition>` child's `from` in document order.
- `<transition from="..." to="..." weight="1.0">` — `from`/`to` required
  non-empty; `weight` optional float, default `1.0`. **No separate Pydantic model**
  in CE — parsed by hand inside the state-machine parser, not dispatched as its own
  element. `<state-machine>` accepts only `<transition>` children (and `<comment>`);
  anything else, or zero transitions, raises.
- Legal only directly under `<setup>` (a setup-time registration element, like
  `<memstore>`) — NOT inside `<generate>`.
- **Runtime engine** (this is the substantive part to port):
  - The definition (`rules: list[(from, to, weight)]`, `start`) is registered once,
    addressable later purely by `id` via `generator="<id>"` — same generator-lookup
    mechanism as any other named generator.
  - Each `generator="<id>"` **reference** instantiates its own **independent,
    stateful walker** — critical: two separate `<generate>` blocks referencing the
    same machine id must each start their own walk at `start` and never share
    state (CE test confirms this explicitly). Do not cache/share the walker
    instance across references.
  - `generate()` (per record): return the current state, then advance. Multiple
    transitions from the same `from` state → weighted random choice
    (`random.choices`, **with** replacement, i.e. self-loops are legal and can
    repeat) using the run's seeded RNG (reproducible under `<setup rngSeed>`).
    A state with no outgoing transitions is **terminal**: emitted once, then the
    walk **auto-restarts at `start`** on the next call (not an error, not a stall).
  - Supports convergent paths (multiple `from` states reaching the same `to`) and
    self-loops (`from == to`) naturally — no special-casing needed, both fall out
    of the same weighted-edges-per-state model.

**TDD test list to port (from `tests_ce/integration_tests/test_state_machine/test_state_machine.py`,
4 scenarios — the CE fixture files `state_machine.xml`/`complex_machine.xml` are
good ready-to-adapt worked examples, reproduced in the investigation output this
brief was built from):**

1. A named machine referenced from two separate `<generate>` blocks: every step in
   each walk is a legal transition (or a terminal-state restart); **both walks
   start independently at `start`**, proving no shared/leaked state between
   references.
2. A machine with a self-loop and convergent paths: a long walk (hundreds of
   draws) visits every reachable state including via the self-loop and both
   convergent branches; the self-loop fires at least once.
3. Same machine + same seed → byte-identical walk sequence across two runs;
   different seed → a different sequence.
4. Empirical branch ratios out of a multi-way state converge to the declared
   weights within tolerance over enough draws.

---

## 8. `<demographics>`

**CE spec** (`demographics_model.py`, `demographics_parser.py`,
`datamimic_ce/statements/demographics_statement.py`, `demographics_task.py`,
`datamimic_ce/domains/common/demographics/{loader,sampler}.py`):

- `<demographics dataset="..." version="..." dir="..." rngSeed="...">` — `dataset`,
  `version`, `directory` (XML `dir`) all required; `rngSeed` optional (falls back to
  the setup-wide seed, then an unseeded RNG). Legal only directly under `<setup>`,
  effectively a run-wide singleton (a second `<demographics>` would silently
  overwrite the first in CE — recommend EE either enforce "at most one" explicitly
  or document the override behavior, rather than reproducing the silent-overwrite
  gap).
- **This element produces no output field itself** — it is a setup-time
  side-effect that installs a shared age/sex/condition sampler, built from two
  required CSV files in `directory` (CE's exact filenames: `age_pyramid.dmgrp.csv`,
  `condition_rates.dmgrp.csv` — EE can choose its own file format/schema here if it
  doesn't want to match CE's CSV layout, but the *installation contract* below is
  the part that matters for compatibility):
  - Per-sex age-band weights must sum to 1.0 (within tolerance).
  - Condition prevalence values in `[0, 1]`.
  - Every row's own `dataset`/`version` must match the requested ones, or fail loudly.
- **Consumption contract** (the part downstream code depends on): any entity
  generator that accepts demographic sampling should look up the installed
  sampler/config from the run context and, if the entity supports it, draw
  age/sex/conditions from the installed profile instead of its own defaults.
  In CE this is done **reflectively** (checked via the entity constructor's
  accepted kwargs, not a hardcoded entity allowlist) — recommend EE do the same
  rather than hardcoding which entities are demographic-aware, so new entities
  opt in automatically by accepting the right constructor parameter.
  Per-entity overrides (age min/max, condition include/exclude, a local rng seed)
  are set on the **`<variable>`** referencing the entity, not on `<demographics>`
  itself, and take precedence over the profile-wide config when present — this
  override contract is exercised by CE's `test_patient_demographics` test and
  should not be broken by the port.

**TDD test list**: CE's own coverage here is thin at the *DSL-element* level (one
smoke test) but rich at the *underlying sampler* level. Recommended EE test list,
adapted from CE's full set:

1. `<demographics>` smoke test: descriptor with `<demographics>` + a `<generate>`
   using a demographic-aware entity runs to completion without error.
2. Loader: malformed/incomplete profile data (age bands not summing to 1, missing
   file, dataset/version mismatch) is rejected loudly, not silently accepted.
3. Sampler determinism: same seed → identical sampled age/sex/condition sequences.
4. Sampler distribution: large-N sampled ages statistically match the configured
   weights (a tolerance-based statistical assertion, not exact equality).
5. Override precedence: a `<variable entity="...">`'s own age/condition overrides
   win over the installed profile-wide config when both are present.
6. An entity that does *not* opt into demographic sampling is unaffected by an
   installed `<demographics>` context (proves the reflective opt-in doesn't leak
   into unrelated entities).

This is the largest item in this brief — budget accordingly, and consider shipping
it last, once the smaller items have established EE's own conventions for
setup-singleton elements (state-machine, item 7, is good practice for that pattern
at smaller scale first).

---

## Definition of done (per item)

For each item: EE's own test suite (written first, from the lists above) is green;
`model_json_schema()` on the new/extended model shows a `description` for every new
field (matching this session's CE convention — see `datamimic_ce/model/generate_model.py`
for the target quality bar); the new element/attribute is reachable through EE's
existing autocomplete/schema-generation surface without any manual schema edit
(confirms the registry wiring is correct); and EE's own `spot-guards`/quality CI
jobs (per `.gitlab-ci.yml`) pass unmodified.
