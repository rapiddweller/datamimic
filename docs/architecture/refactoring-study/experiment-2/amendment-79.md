# Amendment 79: insurance coverage producer record

2026-09-30. Decision: Astra. Declare `InsuranceCoverageData` at the existing
`INSURANCE-GENERATORS` boundary. Its producer already projects six required
string fields; the model consumes this record through the allowed
Models → Generators edge. No new module, facade or reversed dependency.

Only the named type is added to the inner public list. Runtime selection,
cache, errors, CSV columns, descriptors and root API stay unchanged.
No broad-type allowance, baseline change or budget increase. This amendment
does not imply complete architecture or descriptor-equivalence acceptance.
