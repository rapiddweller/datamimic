Independent architecture review: link to the review note or approving review (required for changes under `datamimic_ce/`).

Equivalence classes: list the input classes and boundary values of the changed behavior (valid, invalid, empty, missing, duplicate, min-1, min, max, max+1). Name each class you leave out and say why.

- [ ] Every listed class has a checked-in DSL descriptor (a scenario under `tests_ce/scenarios/` or a one-line patch negative), or a written reason why not.
- [ ] A negative control shows that the check can fail for the stated reason.
