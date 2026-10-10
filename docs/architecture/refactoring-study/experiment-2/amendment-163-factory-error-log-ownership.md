# Amendment 163 — factory error-log ownership

Date: 2026-10-08. Decision: Astra-approved scoped logging correction.

For a missing factory entity, `RuntimeRunSession.execute()` owns one ERROR
record. Validation raises the existing `ValueError` without a redundant local
log. Native `create()` and `create_batch(2)` probes confirmed two records before
the correction; the retained record is `Value error: Entity name 'missing'
not found in the XML model`.

Preserve exception class, args, text and cause/context; constructor logging,
outer catch/rethrow, lookup order, warnings and successful validation mutations.
Direct private validation no longer logs this error. Traceback line numbers may
shift. This changes neither generated data nor descriptor/error payloads.

This is not a global log-once rule or CE/EE stream/class equivalence. It grants
no architecture allowance and changes no oracle, baseline or frozen input.
