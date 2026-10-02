# Amendment 80: Authoring verdict-policy ownership

2026-09-30. Decision: Astra. Pure acceptance and verification policies move
from Application to Domain. Their four existing bounded-capture records move
from the execution adapter into `authoring/contracts.py`. Application keeps
run/replay sequencing; the adapter produces evidence. No new DTO or shim.

Declare only the eight policy operations used by the service at the local
Domain boundary. Preserve Domain's no-Adapter requirement. Update exact
module targets and responsibility sentences; retain eight meaningful Domain
children with an explicit cohesion rationale. EE receives the same target,
not a silent algorithm port. No descriptor, baseline, budget or gate change.
