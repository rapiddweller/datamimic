# Amendment 75: expose the IO context's support type

Date: 2026-09-29. Decision: Astra review, Luna QA, root integration.

`io.api` already exports `ExporterContext`. Its `memstore_manager` property
returns `MemstoreProvider`, but callers cannot import that name through the
facade. Export the existing protocol there. Keep the root contract's public
path at `io.api`; do not publish `exporters.core` as a new direct crossing.
No runtime logic, descriptor, or internal owner changes.
