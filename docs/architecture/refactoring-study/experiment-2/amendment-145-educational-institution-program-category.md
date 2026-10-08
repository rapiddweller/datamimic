# Amendment 145: Educational institution program category

Date: 2026-10-08. Decision: coordinator-approved target clarification.

Assign the existing case-sensitive level-to-program-category mapping to
`EducationalInstitutionGenerator`. The model resolves `level` first, passes its
existing `Path(__file__)` anchor, and keeps the lazy cached property. Preserve
the current precedence exactly: `Elementary`, `Middle`, `High`, higher-education
labels, vocational/technical labels, then `k12`. In particular,
`Higher Education` currently matches `High` first and selects `high_school`.
Program loading, sampling, RNG use, sorting, exceptions, and cache behavior stay
unchanged.
