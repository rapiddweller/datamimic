# Amendment 66: narrow DSL validation boundary

Date: 2026-09-29. Decision: reviewer, following Astra's boundary recommendation
and independent implementation and QA review.

The target incorrectly made the entire `ModelUtil` class public through `dsl.api`.
Authoring uses only five validation operations. Publish those functions instead;
keep the remaining class methods inside DSL models. Declare the existing
`Constraint` union at the DSL root and model boundary because the published
`check_constraints` signature already exposes it. This is a narrower public
surface, not a replacement validator or an exception to `boundary_types`.

Raw XML attributes remain open mappings until model validation. We do not
introduce a DTO that would misrepresent their runtime shape. ArchKeel still
reports one `Constraint` position despite the exact alias declaration; retain
that finding for analyzer review rather than suppressing it.
