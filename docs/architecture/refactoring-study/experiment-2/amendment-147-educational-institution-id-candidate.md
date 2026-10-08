# Amendment 147: Educational institution ID candidate

Date: 2026-10-08. Decision: coordinator-approved target clarification.

Assign the existing `EDU-` prefix and eight hexadecimal RNG draws to
`EducationalInstitutionGenerator`. `EducationalInstitution` retains the
uniqueness claim and lazy cached property. Preserve one public RNG lookup,
ordered draws, constructor child-RNG derivation order, candidate-before-claim
behavior, and the existing registry collision, failure, cache, and
property-evaluation semantics. The generator does not retry or enforce
uniqueness.
