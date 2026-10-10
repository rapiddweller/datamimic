# Publication UNKNOWN review

2026-10-10. Astra decision; CE `cd6b1666`, published ArchKeel 1.1.0.

All 19 `interface.usage_unknown` validation diagnostics concern 15 Domain
models. Their service classes expose matching generic return-type candidates,
but have `source_member_binding_static=false`. Generic substitution works;
the checker cannot prove the service member surface remains unchanged.
These validation diagnostics are separate from the 254 canonical UNKNOWN records.

Example: `domains.api` publishes `CityService`, which binds
`BaseDomainService[City]` and inherits `generate() -> T` / `generate_batch() ->
list[T]`. The example constructs the service; the registry also stores service
classes as values. These are real consumers, not missing public declarations.

Seven isolated cases on 1.1.0 confirm the limit: annotation-only use proves
the generic publication; construction, class-value escape and mutation retain
only a candidate. The unrelated `Noise` model stays unused. The existing
upstream `test_constructed_generic_facade_retains_candidate_publication` also
expects construction to remain UNKNOWN. This is not an upgrade regression.

Keep CE code and public declarations unchanged. A future ArchKeel refinement
must prove specific construction/escape paths safe while preserving UNKNOWN
for mutation, unknown callbacks and construction hooks. A simple-constructor
improvement alone would not settle CE's custom constructors and class registry.
All 19 diagnostics and native amendment binding remain OPEN.

LOCAL VERIFIED: complete diagnostic-to-candidate mapping, checker source trace
and seven isolated cases; no new CE scan or runtime-equivalence claim.
CI-ONLY VERIFICATION: none for this review. Reproducer, assertions and receipts:
`/tmp/ce-resume-20261010/usage-unknown/`.
