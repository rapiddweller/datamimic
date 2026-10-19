# Make the model reviewable

The user must be able to inspect what the model will do and what was proved
without reading transient DM JSON or interpreting a large tool response.
Build this review from the original request, actual XML and actual evidence.

## Before execution

Show a compact model outline. For each product or nested field, identify its
purpose, count per parent, total count, source and destination. Distinguish an
embedded object/list from separately generated rows. Show the hierarchy as a
small tree or relationship diagram when it helps explain the model.

List primary and foreign keys in order, including every component of composite
keys and the exact parent join. Local identifiers that repeat across parents
are not globally unique. Separate membership checks on individual columns do
not prove a composite relationship. Discover supported checks from the runtime;
retain an independent tuple/SQL assertion when it cannot express the requirement.
Mark that assertion as separate evidence, never as a built-in certificate.

State the seed and relevant generator choices with a short reason. Name every
file/database/table that real execution would read or change, the operation and
expected scale. Record assumptions that affect the requested result. For an edit,
summarize the XML changes and resulting count, relationship or destination changes.

## Inspect the executable project

Map each business rule to its XML location and parameter source. Explain the
execution order and which outputs each file or helper serves. Identify any
Python function, its typed input/output contract and why the algorithm belongs
there. Keep field operations and projections visible at the fields they affect.
Show where a person can change a rule and how its effects will be verified.

For global selection, include decision reasons and the relevant rule values.
A search budget exhausted is not proof of infeasibility. Prepare and validate
complete output before destructive steps; state whether cleanup and delivery
have an established common transaction. A separate report cannot compensate
for an opaque executable model.

## Report evidence

Keep one row for every original requirement, including unsupported requirements:

| Requirement | Model location | Expected | Observed | Check and evidence | Status |
|---|---|---|---|---|---|

Use measured values and link to the actual receipt, readback or assertion output.
Use passed, failed or not checked. Explain failures and unknowns plainly. An
omitted check is not a pass; report partial task completion even if Build is ready.

Include a few representative rows that expose joins and nesting, clearly labelled
as samples. Show observed totals and capture completeness separately. Explain
bounded verification versus requested full-run scale, requested versus completed
smoke/replay, and external delivery versus target-isolated capture. Real database
delivery needs readback and integrity queries; a sample cannot prove whole-table
uniqueness or composite foreign keys.

## Deliverables

For local projects, return clickable paths to:

- `model.xml`: the exact compiled XML from the successful operation.
- `model-review.md`: the model outline, requirements table, samples and limits.
- `model-proof.json`: the unmodified operation response, retained as evidence,
  not as an editable model or a replacement for the original requirements.

Return the independent assertions/readback when they establish additional claims.
Use the project's requested names when present. For Platform projects, use the
existing file/commit workflow and link the same review information to its saved
model and execution identity; do not write local files as a substitute.

On rejection, retain diagnostics and a concise incomplete review. Label review
XML as a candidate until separately requested runtime execution and independent
acceptance establish their own evidence. Preserve the bounded rejection even
then; normal runtime success does not create a Ready Build certificate.
