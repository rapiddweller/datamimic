# Amendment 154 — lazy model computation ownership

Date: 2026-10-08. Decision: Astra-decided target clarification.

Keep cached model properties at their owner only when extraction would change
observable lazy reads or RNG order. This is not general permission for models to
generate independent values; generators own independent rules over resolved
inputs. Preserve public getter/access and RNG order. Do not add callbacks or
staged-state abstractions to relocate orchestration.

The exceptions are distinct: `Order.discount_amount` draws eligibility before
lazy product and price reads, then draws the rate; `EducationalInstitution.founding_year`
reads the reference year and conditionally accesses its public `type` property;
`MedicalDevice.specifications` draws common values before lazy device-type access
and interleaves type-specific draws with generator helpers. `MedicalProcedure.cost`
already owns its cached calculation because it reads other lazy clinical properties
between RNG draws. This amendment clarifies responsibility only; it does not claim
the broader architecture is complete.
