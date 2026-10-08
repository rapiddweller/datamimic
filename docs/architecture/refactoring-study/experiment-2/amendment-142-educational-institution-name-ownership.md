# Amendment 142: educational-institution name ownership

Date: 2026-10-08. Decision: coordinator-approved target clarification.

Assign institution-name candidate construction and random choice to
`EducationalInstitutionGenerator`. `EducationalInstitution` resolves city,
state, type, and level in order, then retains its lazy cached property.
