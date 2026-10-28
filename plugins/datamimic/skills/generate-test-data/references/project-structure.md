# Project structure

Build every local CE dataset as a project directory, even a small one. People
review the files; Build proves them.

```
<project>/
├── datamimic.xml                entry: process comment, seed, clients, memstore, lib loading, ordered includes
├── conf/base.properties         parameters; <env>.env.properties for connection settings
├── model/<nn>_<activity>.xml    generation, one activity per file: 10, 20, 30 …
├── delivery/<nn>_<activity>.xml export, insert or upsert into targets: 90+; the only writers (rule 3)
├── data/
│   ├── entity/*.ent.csv         business data and code lists
│   ├── weighting/*.wgt.csv      distributions
│   └── fixtures/*.ent.csv       deliberately chosen cases, such as the rows behind a negative test
├── lib/*.scr.py                 named functions with typed inputs and outputs
├── sql/*.scr.sql                schema, cleanup and delivery SQL (real runs only; Build refuses SQL execute)
├── acceptance/build.json        expectations, product roles, verification
└── README.md                    purpose, process, rule → file table, evidence
```

Data files are UTF-8 and use the default pipe `|` separator. Never set
`separator=","` or `defaultSeparator=","`. An `.ent.csv` file has one header row.
A `.wgt.csv` file has no header; each line is `value|weight`.

Leave out folders the task does not need. Keep the entry at `datamimic.xml`.

## Separation rules

1. Business data, code lists and distributions live in `data/`, not as literals
   spread over XML. Deliberately chosen cases live in `data/fixtures/`, never in
   id arithmetic.
2. Clients and the memstore are declared in the entry. Steps never declare
   clients; Build refuses them there. Declare the memstore as `<memstore id="mem"/>`:
   EE ignores the declaration (warning W005) and always provides `mem`, so only
   this id runs in both editions.
3. `model/` steps write only to the memstore. `delivery/` steps read it and are the
   only ones that write to files, databases or brokers. Name a delivery step after
   its activity, for example `delivery/90_validate_output.xml`. Two exceptions put
   a step that is not an export in `delivery/`:
   - A check step that writes its check products is a delivery step. Number it
     before the cleanup and the exports, so that it checks the complete output.
   - A cleanup step that deletes the rows of an earlier run is a delivery step.
     Number it after the checks and before the exports.
4. Logic that spans tables is a named function in `lib/`. The model passes every
   input in; the function returns its decisions and fails loudly when a rule cannot
   be met.
5. The entry shows the process: one comment line per step, includes in execution
   order, each a literal path such as `<include uri="model/10_customers.xml"/>`.
6. `acceptance/build.json` holds every requirement as an expectation or role. It
   survives edits to the XML, so do not restate requirements elsewhere.

Product names are unique across all files. Includes are literal setup-level paths
inside the project. Build reads the entry with all its steps, so expectations and
`product_roles` may name products of any step.

## Finish

Run `datamimic authoring build <project>` and repair until `outcome: "ready"`.
Its `artifact.files` lists every file the proof read with a digest. Write the
README last; Build does not read it, so writing evidence there keeps the proof.
