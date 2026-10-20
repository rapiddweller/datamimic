# Authoring project mode and project contract

Status: **decided in direction** (Alex, 2026-10-20): a new `BuildRequestV5` for CE and EE, CE
first and then EE (datamimic-ee#69); custom Python runs with safe globals. The project layout
below is a measured proposal that replaces the `datamimic-demos` layout as the reference.

## Context

Authoring today proves **one** XML file. A Build transaction carries one DM JSON document,
compiles it to one `compiled_xml` and certifies that file. The agent plugin follows suit: its
deliverable is `model.xml`, `model-review.md` and `model-proof.json`.

Real DATAMIMIC projects are not one file. `datamimic-demos` (for example `demo-py-scripting`,
`demo-database-basics`, `demo-insurance-claims-360`) use an entry descriptor that shows the
process and includes step files, plus `conf/`, `entity/*.ent.csv`, `weighting/*.wgt.csv`,
`script/*.scr.py|*.scr.sql` and `template/`. That split is the human review surface: business
data, parameters, custom logic and delivery each live in one place.

Evidence (2026-10-20, CE `aa0fbb3a`):

- **Blind tests.** 12 isolated agent sessions (no project context) built 6 scenarios. 11 reached
  Ready and their data was correct, but every project was a single XML file. Cross-table rules
  were satisfied only by construction, often through id arithmetic that a reviewer cannot follow.
- **Reference project.** The flight-school scenario was rebuilt by hand in the target structure.
  The real run met all rules R1–R5 and the negative cases, with no duplicates.
  Authoring could not prove it:

| Operation | Result |
|---|---|
| `lint` / `compile` ↔ `decompile` of the entry | works, including `execute` and comments |
| `dry-run` with includes, `.ent.csv`, memstore | works (#346) |
| `dry-run` with `<execute uri="script/*.scr.py">` | refused: no bounded policy (`dryrun.py`, #332) |
| `build` with any `<include>` | refused: `unsupported_bounded_operation`, even for `.properties` |
| `decompile` of a step file | judged standalone and rejected: seed, memstore and scripts belong to the entry |

Without a project-level proof, an agent that wants `outcome: ready` is pushed back into a
monolith. Steering in the plugin alone cannot fix that.

## Decision 1 — Project contract

A DATAMIMIC project is a directory with one entry descriptor. The `datamimic-demos` layout was the
starting point. The layout below improves it in three ways:
- folders separate *what* is generated from *where* it goes;
- numbering leaves gaps so steps can be inserted later;
- the acceptance inputs become project files instead of being lost after every Build.

```
<project>/
├── datamimic.xml                entry: process comment, seed, clients, memstore, lib loading, ordered includes
├── conf/                        base.properties (+ <env>.env.properties): parameters, connection settings
├── model/<nn>_<activity>.xml    business generation, one activity per file, numbered 10, 20, 30 …
├── delivery/<nn>_<target>.xml   export, insert, upsert into targets, numbered 90+; the only writers
├── data/
│   ├── entity/*.ent.csv         business data and code lists
│   ├── weighting/*.wgt.csv      distributions
│   └── fixtures/*.ent.csv       explicitly chosen cases (appointments, edge cases behind negatives)
├── lib/*.scr.py                 named pure functions with typed inputs and outputs (safe globals)
├── sql/*.scr.sql                schema, cleanup and delivery SQL
├── template/                    document templates
├── acceptance/
│   ├── build.json               expectations, product roles and verification for this project
│   └── *_oracle.py | *.sql      independent checks for rules no expectation can express yet
└── README.md                    purpose, process, rule → location table, evidence
```

Measured on the flight-school reference project. `model/`, `delivery/`, `data/` and `lib/`
resolve relative to the entry (included contexts keep the entry directory). With the same seed
the output is byte-identical to the flat layout, and the independent oracle confirms R1–R5 and
all negatives.

Separation rules:

1. Business data and code lists live in `data/entity/` and `data/weighting/`, never as literals
   spread over XML. Deliberately chosen cases live in `data/fixtures/`, never in id arithmetic.
2. Parameters and connections live in `conf/` and the entry; `model/` files never declare clients.
3. `model/` writes only to the memstore. `delivery/` reads it and is the only place that writes to
   files, databases or brokers, so a target can change without touching business logic.
4. Logic that spans tables is a named function in `lib/`. All inputs are passed in from the model,
   so the function does not read state; it returns its decisions and fails loudly when a rule
   cannot be met.
5. The entry shows the process: one comment line per step, includes in execution order.
6. `acceptance/build.json` is the single source of the project's acceptance. Editing XML no
   longer loses the requirements, because they no longer exist only in the transaction.

## Decision 2 — Build project mode

Add a Build operation that proves a project rather than a document.

```mermaid
flowchart LR
  A[Agent edits project files] --> L[lint/compile each XML in project context]
  L --> B[Build project: entry + expectations + roles]
  B --> X[Bounded run of the include graph in a private workspace copy]
  X --> C[Acceptance over products from all files]
  C --> R[Ready: digest of every project file + evidence]
```

- **Protocol:** `BuildRequestV5`, CE first, then the paired EE port. Input: the project root and
  `acceptance/build.json` (entry path, expectations, product roles, verification). The files in the
  workspace are the model; there is no second DM JSON copy of them. `V4` stays for single-document
  callers until a migration is decided.
- **Graph:** literal includes as in #346: `.xml` steps, `.properties`, and the resources they
  read. Expectations address products by name across all files; product names stay unique per project.
- **Proof binding:** Ready carries a digest per project file (XML, conf, entity, weighting, script).
  Any change to any of them invalidates the proof.
- **Project context for single files:** `lint`, `compile` and `decompile` of a step file use the
  entry's context (seed, memstore ids, properties, loaded script symbols), so a step is not judged
  as if it were standalone.
- **Diagnostics** name the file and line of the failing element in an included file. Values
  stay redacted; only file names, paths and element tags appear.

Recommended over the alternatives:

| Option | Choose when | Trade-off | Main risk |
|---|---|---|---|
| **Project Build over workspace files (recommended)** | the project files are the product | new operation; acceptance projection must read the XML graph | protocol change for CE and EE |
| Multiple DM JSON documents per transaction | agents must not edit XML directly | keeps the codec as the only writer | two representations of every file to keep in sync |
| Keep single-file Build, plugin splits afterwards | short term only | no engine change | the proof does not cover the delivered project |

## Decision 3 — Custom Python with safe globals (#332)

`<execute uri="lib/*.scr.py">` loads a **pure function library**. The module runs with the same safe
globals as DSL expressions, not with a full `exec`:

- CE `engine/runtime/scripting/expression_globals.py` mirrors EE's `SAFE_GLOBALS` (EE ADR-031).
  It provides curated stdlib names and no builtins.
- Under `rngSeed`, `random` and the clock are seed-bound proxies, and entropy sources raise.
  Helper functions are therefore reproducible without extra rules.
- Imports are not allowed; the safe globals already provide `random`, `datetime`, `math`, `re`,
  `json`, `itertools`, `collections`, `statistics`, `hashlib` and `base64`. The one exception is
  `from __future__ import annotations`, which compiles away.

A static check of the module's AST runs before execution. It admits only these top-level statements:
docstring, `def`, constant assignments and the `__future__` import. Anything else is refused with a
typed diagnostic that names the file and the statement line.

Measured: the reference project's `lib/personnel.scr.py` loads and runs under the CE expression
globals once its `__future__` import is stripped. The helper namespace still needs two additions:
- exception types such as `ValueError`, because a function must be able to fail loudly;
- `__build_class__`, but only if classes are admitted at all.

Safe globals are a contract for determinism and intent, not a security sandbox. The isolation
boundary stays the bounded child process with its private workspace. `sql/*.scr.sql` and
`execute target=<client>` stay outside bounded proof. Their delivery needs a real run with
readback, reported separately: target-isolated capture does not prove external delivery.

## Decision 4 — Plugin steering

The plugin's deliverable becomes the project tree:

- `references/project-structure.md` holds Decision 1. The workflow scaffolds the layout, writes data
  to `data/`, keeps cross-table logic in `lib/` and delivery in `delivery/`, and maintains
  `acceptance/build.json`.
- `review.md` reviews per file: purpose, inputs, outputs, rules located there. It keeps the
  requirement → location → evidence table and the project-wide proof.
- The engine pitfalls the reference project hit are part of the guidance until the engine fixes
  them: records are `DotableDict` (`get()`/attribute access, no item access), keys hold no lists,
  `<variable>` has no `min`/`max`, and a nested `count` evaluates in the enclosing record.

## Acceptance

1. The flight-school reference project reaches Ready through project Build. Its expectations
   cover R1, the volumes and the negatives, and an independent oracle confirms R2–R5.
2. A change to any project file invalidates the proof.
3. A failing element in a step file reports that file and line, without values.
4. A `lib/` module with an import, a top-level call or a file write is refused and names the line.
   Seeded `random` inside a helper replays identically.
5. Blind rerun (12 isolated sessions) scores project structure as well as correctness. The rubric
   covers layout, data in `entity/`/`weighting/` instead of literals, delivery steps separate from
   generation, and a readable entry process.

## Decisions taken (Alex, 2026-10-20)

1. Layout: the `datamimic-demos` structure was a starting idea; this document proposes the measured layout above.
2. Protocol: `BuildRequestV5` for CE and EE; CE first, then EE.
3. Python: allowed as pure libraries running with safe globals.

Still open: whether `class` definitions are admitted in `lib/` (needs `__build_class__`), and when
`V4` is retired.

## Not decided here

Cross-table expectation kinds (conditional composite foreign key, unique per filtered group,
multi-column duplicates, date ranges) are a separate decision. They make R2–R5 checkable as
expectations instead of only by an independent oracle.
