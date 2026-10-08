# Amendment 162 — declare the IO client names boundary

Date: 2026-10-08. Decision: Astra.

`ExporterContext.clients` needs membership and ordered name enumeration.
`ClientNames` describes those existing operations. Client retrieval remains
`get_client_by_id`; the separate `ClientLookup` keeps its `.get` requirement.
Dictionaries and compatible injected registries need no adapter or probe.

Declare exactly `datamimic_ce.engine.io.clients.client:ClientNames` in root
`COMP-IO.public`. The existing `IO-CLIENTS` module declaration owns the type.
Keep dispatch, method lookup, diagnostics and native errors unchanged.
Add no dependency permission, re-export, selector, allowance or baseline exception.
