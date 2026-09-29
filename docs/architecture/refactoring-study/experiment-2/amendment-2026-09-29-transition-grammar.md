# Transition grammar owner

Date: 2026-09-29. Decision: Astra, under the delegated EE-led 5.0 target.

The `<transition>` attributes were checked only inside the parser. Declare
`engine/dsl/model/setup/transition_model.py` as their owner and let the parser
consume that model. The DSL model registry now exposes `from` and `to` as
required strings and `weight` as an optional positive float with default 1.0.
The model type is public only at the root and nested DSL-model boundaries
because the parser and registry import it directly.
This changes only the `elements.transition` authoring-capability projection;
it does not add a new XML feature or change valid descriptor output. Invalid
transitions fail at the model boundary, so their error wording may change.

This is a prerequisite for a registry-derived DM JSON codec, not evidence that
the EE authoring contract has been adopted. `echo`, `condition`, and `else`
metadata still need explicit ownership before that codec can be complete.
