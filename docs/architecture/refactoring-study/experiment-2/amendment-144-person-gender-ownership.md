# Amendment 144: Person gender ownership

Date: 2026-10-08. Decision: coordinator-approved target clarification.

Assign demographic sex normalization and fallback selection to
`PersonGenerator`. `Person` passes its already-reserved demographic sample and
keeps the lazy cached property. Preserve the accepted prefixes and use the
existing gender generator only for unrecognized labels.
