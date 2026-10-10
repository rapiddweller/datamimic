# Amendment 161 — declare the IO client lookup boundary

Date: 2026-10-08. Decision: Astra.

`has_mongodb_upsert_target` accepts a registry providing only
`get(key: str, /) -> RegisteredClient | None`. `ClientLookup` describes that
existing operation; dictionaries and compatible injected registries need no
adapter or runtime probe.

Declare exactly `datamimic_ce.engine.io.clients.client:ClientLookup` in root
`COMP-IO.public`. The existing `IO-CLIENTS` module declaration owns the type.
The previous parent boundary omitted a type now exposed by the IO function.

This explicitly adds one public type. It adds no convenience re-export,
dependency permission, package selector, boundary-type allowance or baseline
exception. Keep the original Runtime calls and routing body unchanged,
including registry identity, argument order, delayed method lookup and native
errors. The SQL cast remains separate open debt.
