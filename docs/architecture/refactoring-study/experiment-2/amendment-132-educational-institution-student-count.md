# Amendment 132: educational institution student-count ownership

Date: 2026-10-08. Decision: coordinator-approved target clarification.

Assign student-count branch selection and sampling to
`EducationalInstitutionGenerator`. `EducationalInstitution` resolves type then
level and retains its lazy cached property.

Preserve branch precedence, inclusive bounds, one public RNG access/draw, and
student/staff evaluation order.
