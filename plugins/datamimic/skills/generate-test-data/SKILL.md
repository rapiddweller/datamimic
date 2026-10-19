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

The plugin contains usage instructions. Discover vocabulary and schemas from
the selected runtime; CE and EE capabilities are not interchangeable.

## Preserve the task

Record the requested row counts, child counts, relationships, allowed values,
ranges, time windows and delivery destination before building. Convert each into
an explicit acceptance check. Check the result against that original list so an
omitted requirement cannot disappear behind a successful Build.

XML is the persisted executable model. DM JSON is a transient agent view;
expectations and identifier/FK declarations are Build transaction input. Supply
those requirements again when editing existing XML.

Repair structured diagnostic codes, paths and remediations, then retry with a
changed candidate. If the requested behavior is unsupported or a failure repeats
without a justified repair, report the blocker with the diagnostic and preserve
the user's requirements.

## Report the actual proof

A ready compile proves syntax. A ready Build additionally proves its declared
acceptance against a complete bounded capture. Sample rows are not total counts.
Smoke/replay pass only when requested and reported as passed. Target-isolated
capture does not prove delivery to an external database or file destination.

Return the XML path, declared checks, observed counts, requested verification
results and any remaining limitation. Execute the real descriptor only when the
user requested execution, using the selected project's execution interface.
