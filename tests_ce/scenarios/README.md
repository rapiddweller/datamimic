# Scenario corpus

A scenario is a complete project, written the way an agent writes it. The project is the test.
One Python module, `test_scenarios.py`, runs every scenario. It holds no project logic.

## Layout

```text
<id>/datamimic.xml           the entry descriptor
<id>/model/ delivery/ lib/   optional steps and helpers, as the project needs them
<id>/acceptance/build.json   the business rules Build must prove
<id>/scenario.json           what the scenario promises (see below)
```

The id starts with `s`, a two-digit number and a short name, for example `s02_parent_child`.

## `scenario.json`

| Field | Meaning |
|---|---|
| `title` | One short line. |
| `proves` | A list of short sentences. Each sentence is a fact the scenario shows. |
| `products` | Product name to expected row count of a normal run. |
| `negatives` | A list of `{"name": "<name>", "patch": {"file": "<path>", "old": "<text>", "new": "<text>"}, "diagnostic": "<code>", "expected": "<text>"}`. The patch replaces one text in one file of a copy of the project. The old text must occur exactly once. The file must stay inside the copy. `expected` is optional. Use it when one code covers several rules (for example `row_condition`): it is the `expected` text of the diagnostic, which names the rule. |

A negative `diagnostic` is a code that Build reports, for example `exact_count` or `DM315`.
Build must reject the variant, and the code must be in the list of diagnostics.
A negative can also give `run_error`. Then a normal run of the variant must stop with a `TaskConfigError` that contains this text.

## What the test does

For each scenario directory the test:

1. Copies the project to a temporary directory.
2. Builds it and checks that the outcome is `ready`.
3. Runs it and checks the row count of each product in `products`.
4. Runs it a second time and checks that the rows are identical.

For each negative the test copies the project, applies the patch to the copy, Builds it, and checks the rejection and the code.

## Add a scenario

1. Write the project under `tests_ce/scenarios/<id>/`. Set `rngSeed` on `<setup>`.
2. Write each business rule as an expectation or role in `acceptance/build.json`.
3. Run `datamimic authoring build tests_ce/scenarios/<id>` until the outcome is `ready`.
4. Write `scenario.json`.
5. For each rule, write one patch in `negatives` that breaks that one rule (for example in `datamimic.xml` or `acceptance/build.json`).
6. Run Build on the variant. Copy the code it reports into `negatives`.
7. Run `pytest tests_ce/scenarios -q`.

## Rules

- Use no real data and no customer names.
- Use only file, SQLite or targetless products here. A scenario that needs a service goes to `external_service_tests`.
- Set `max_count` in `acceptance/build.json` when the project makes more than 10 rows in total.
- Break one rule in each negative. Then the code in `scenario.json` names the cause.
- A defect that a scenario finds gets its own fix and its own test, or a documented limit.
