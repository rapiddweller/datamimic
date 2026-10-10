# Amendment 99: Medical-procedure cost ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved target clarification.

Keep the cached `MedicalProcedure.cost` calculation model-owned. Its uncached
draw order is surgical flag, base-cost draw, anesthesia flag and conditional
draw, duration (including its cached surgical flag), hourly cost draw, then
variation. Eager generator arguments would evaluate lazy properties earlier
and change seeded outputs. Fragmenting this coupled sequence into generator
helpers adds boundaries without moving ownership of its ordering or caches.

`MedicalProcedureGenerator` continues to own independently callable procedure
values and duration draws; this exception does not authorize other model-owned
generation.
