# Haiku CLI authoring evaluation — 2026-07-15

This is a curated outcome record, not an agent transcript or a portable
reliability benchmark. Generated models and runtime evidence are intentionally
not committed.

## Reported outcomes

The evaluation owner independently checked three delivered business outcomes:

| Axis | Result |
|---|---:|
| Business outcomes satisfied | 3/3 |
| Canonical `model.dm.json` authoring | 2/3 |
| Raw-XML fallback incidence | 1/3 |

The raw-XML fallback counts as successful business delivery, but not as a
canonical authoring pass. Combining those axes into one 3/3 authoring score
would hide the interface failure under evaluation.

## Independently reproduced repository friction

Separate repository probes reproduced the relevant canonical-tooling gaps:

- an unknown field inside a memstore source reported the enclosing product
  instead of the exact source-union owner;
- bounded count evidence exposed the required higher limit but no typed retry
  action;
- a missing consumer foreign-key role was only described in prose; and
- the typed reference catalogue could not request a memstore-source fragment.

Focused repository changes and regression tests address those boundaries through
model-derived repair, service-owned bounded-run remediation, structured role
evidence, and source-specific reference queries. These probes validate the
tooling behavior; they do not independently reconstruct the model conversation.

## Weighted sample limitation

One seeded count-50 probe produced 50 unique IDs, no value outside the requested
domain, and a deterministic replay match. The observed 37/13 split for 8/2
weights is one sample only. It proves domain membership and replay for that run;
it does not prove distribution calibration or a model's statistical reliability.
