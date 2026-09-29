# Group generator definitions

Date: 2026-09-29. Decision: Astra.

`engine/dsl/model/setup` has nine direct modules after the typed transition
model. Three define named generators: `GeneratorModel`, `StateMachineModel`,
and `TransitionModel`. Move those three into `setup/generators/`, leaving seven
direct setup children. This group has one concern; it is not a count-only
wrapper and introduces no facade, API shim, or new runtime behavior.

Update exact module targets, public symbol paths, and root-layout rules.
Declare the same future physical paths for EE; its current checkout is not
changed by this CE step. Keep model schemas and valid descriptor outputs
unchanged.
