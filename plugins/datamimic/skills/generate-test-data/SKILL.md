---
name: generate-test-data
description: Create and verify synthetic datasets, database seeds, or pseudonymized exports with DATAMIMIC. Use for new test data or edits to existing DATAMIMIC models.
---

# DATAMIMIC test data

Turn the user's data requirements into an executable model and evidence that
checks those requirements. Keep their requested outputs, relationships and scale.

## Choose the project

- For a local project, use [CE authoring](references/ce.md). The project CLI is
  the baseline; an existing CE MCP connection exposes the same application.
- For a connected DATAMIMIC Platform project, use [Platform authoring](references/platform.md).
  Its project-scoped MCP server owns the workflow and remote files.
- If both are available and the destination is unclear, clarify the destination
  before changing files or configuring a connection.

The plugin owns the workflow and human review. Discover purpose, vocabulary,
attributes, generators, field types and schemas from the selected runtime,
using focused queries. Do not duplicate DSL knowledge in the plugin or load a
separate DSL skill. CE and EE capabilities are not interchangeable.

## Preserve the task

Record the requested row counts, child counts, relationships, allowed values,
ranges, time windows and delivery destination before building. Convert each into
an explicit acceptance check. Check the result against that original list so an
omitted requirement cannot disappear behind a successful Build.

XML is the persisted executable model. Expectations and identifier/FK declarations
live in the project's `acceptance/build.json`, so they survive edits to the XML.
DM JSON is a transient agent view of one XML file.

Repair structured diagnostic codes, paths and remediations, then retry with a
changed candidate. If the requested behavior is unsupported or a failure repeats
without a justified repair, report the blocker with the diagnostic and preserve
the user's requirements.

## Build a project people can understand

The executable XML and its supporting files are the human review surface.
Use native field operations, sources, types, relationships, conditions, checks
and projections wherever they express the intent clearly. Give each file a
named activity and each extra field a real consumer. Keep shared rule parameters
in one place; distinguish rules, demand and source data.

Use a named Python function when an algorithm is clearer there, such as global
assignment with backtracking. Give it typed inputs and outputs and one purpose.
Keep model-owned rules, parameters and data access visible in the model; pass
prepared inputs into the algorithm and return decisions with their reasons.
Expose execution order in the entry model. Validate the complete planned output
before cleanup or external writes. Preserve separate outcomes for a solution,
proven infeasibility and an exhausted search budget.

## Report the actual proof

A ready compile proves syntax. A ready Build additionally proves its declared
acceptance against a complete bounded capture. Sample rows are not total counts.
Smoke/replay pass only when requested and reported as passed. Target-isolated
capture does not prove delivery to an external database or file destination.

Follow [the model review contract](references/review.md). Return a readable model
outline and a requirement-to-evidence table with the XML and raw proof. A ready
receipt cannot replace this review or independent checks for requirements the
runtime cannot express. Execute the real descriptor only when the user requested
execution, using the selected project's execution interface.
