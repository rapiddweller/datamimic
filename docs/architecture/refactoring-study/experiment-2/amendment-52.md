# Amendment 52: publish the IO export session

Date: 2026-09-28.

The frozen IO contract listed exporter construction functions but no typed owner
for per-worker registrations and page dispatch. That left Runtime storing
concrete exporter lists. Publish `ExportSession` from the existing IO registry
through `io.api`; Runtime retains page and child ordering. This changes one
declared IO interface, not a dependency direction or DSL behavior.

The candidate ArchKeel report initially found `io:IO-INTERFACES` at this new
crossing. Adding the explicit public symbol removed that violation. Buffered
finalization and publication remain a separate IO-ownership step.
