# Amendment 177 — converter value boundaries

2026-10-09. Decision: Astra, delegated architect. Base `184e1edbd6a2fff0185fa32878a78831470d400b`.

Converter is a polymorphic extension boundary: the chain receives native Python
values, and each implementation owns its validation and errors. A finite DTO or
closed union would exclude custom values and extension results. Structural
conversion also returns arbitrary non-container values by identity.

Approve only the 19 enumerated direct `object` / `object | None` positions in
DOMAIN-API-TYPES: 12 specialized inputs, base input/output, CustomConverter
context/input/output, and structural-converter input/output. CustomConverter
stores extension-supplied context unchanged; its public contract does not require
a concrete Runtime context or a Domain-to-Runtime dependency.

Specialized output types, constructor controls and unrelated context parameters
remain constrained. No Any, missing annotation, wildcard, DTO-field or container-
depth selector is admitted. Existing provenance-map permission stays unchanged.
This explicitly supersedes Step117's agent decision to retain these 19 findings;
its behavioral evidence and all other Step125 dispositions remain unchanged.
The prior finding was a real target mismatch, not a checker defect.

This is accepted opacity, not type closure or runtime validation proof. Domain
keeps its existing agent attribution. Source, public/dependency grants, ownership,
baseline and oracle are unchanged. Full DSL/EE compatibility, evaluated UNKNOWNs
and all-depth report acceptance remain open.

LOCAL VERIFIED: independent converter review, 19 actual-record positives and
28 negatives, including an opaque specialized return and unrelated controls.
The combined report removes exactly these 19 and Amendment176's four findings;
all other findings/UNKNOWNs remain exact. Combined checks, limits and unbound
widenings are recorded in [Amendment176](amendment-176-native-map-boundaries.md).
CI-ONLY VERIFICATION: pending for the new commit. No runtime behavior was changed
or newly certified by this policy-only packet.
