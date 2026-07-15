# Legacy CLI-only raw-XML agent stress report — 2026-07-14

> Historical pre-canonical evaluation retained for context. It authored raw XML
> and is not evidence for the current `model.dm.json`/`scaffold` contract.

## Isolation contract

- Two independent context-free runs were performed.
- Both were forbidden to read skills, repository source, tests, documentation,
  existing descriptors, or artifacts from the other run.
- Their only DATAMIMIC knowledge source was `.venv/bin/datamimic`: `--help`,
  `capabilities`, `reference`, `scaffold`, `lint`, and `dry-run`.
- A separate black-box process stress used only the executable CLI, never authoring service imports.

## Reproduction flow

```text
business intent
  -> datamimic --help / capabilities / reference
  -> generated descriptor in a system temporary directory
  -> datamimic lint --fail-on warning --format json
  -> datamimic dry-run --sample-rows 50 --format json
  -> external intent oracle over every returned row
  -> identical second dry-run after removing timing_ms
  -> datamimic dry-run --smoke-export --format json
```

## Clean-room result A: nested banking

- Products: 5 branches, 13 customers, 32 accounts.
- All samples were complete (`truncated_rows=false`).
- Unique branch, customer, and account identifiers.
- Every customer branch FK and every account customer/branch FK resolved to its real parent.
- Per-parent cardinalities: 2–3 customers and 2–3 accounts.
- Weighted account-type values stayed inside the requested set; observed counts were
  checking 20, savings 7, business 5. This is not claimed as statistical proof.
- Every sampled balance category matched its threshold.
- Two normalized dry-run hashes were identical:
  `7bd74bf3f977d753aa3fce51dda03c320be81b78d26eddd05c64ec8203e61132`.
- Strict lint and smoke-export both exited 0.

## Clean-room result B: related customer/order/read-back pipeline

- Products: 5 customers, 10 orders, 5 ordered read-back rows.
- All 20 returned rows were complete.
- Customer IDs exactly 1..5; five distinct requested regions.
- Every customer had two orders; local line values were distinct per parent.
- All order IDs were unique and satisfied `customer_id * 100 + line_no`.
- Every order satisfied `net_cents + tax_cents == gross_cents`.
- Read-back preserved every customer ID, region, tier, and credit limit.
- Embedded assertions, strict lint, and smoke-export passed.
- A second run reproduced every generated field; only `timing_ms` changed.

## Black-box process and concurrency result

- Complex customer -> order -> nested line-item scenario: 12 customers, 36 orders,
  131 items; FK, composed-ID, cardinality, and line-total oracles all passed.
- 20 concurrent `scaffold - --format json` processes at concurrency 4:
  20/20 succeeded, stderr was empty, and all samples had one identical hash.
- Wall time 3.81 s; p50 750 ms; p95 805 ms.
- Negative cases produced the expected diagnostics: malformed XML `DM001`, unknown
  element `DM101`, unknown attribute `DM103`, conflicting key sources `DM203`, partial
  time series `DM217`, and runtime script failure `DM002`.

## Defects reproduced and changes made

1. Unknown scaffold kinds silently became empty constants. They are now rejected.
2. Unknown scaffold keys were silently ignored. They are now rejected at root,
   generate, and field level.
3. `rngSeed` was silently ignored. It is now an explicit, reported alias of `seed`.
4. Fractional integer inputs were truncated. Seed, count, integer range bounds, and
   nested-list counts are now validated without lossy coercion.
5. Empty nested lists and range kinds without bounds are now rejected.
6. A zero-row dry-run returned `ok=true`; `DM004` now makes the run unsuccessful.
7. JSON dry-run leaked engine logs on stderr; stdout/stderr are now clean for agents.
8. CLI input limits are shared with MCP/scaffold contracts and printed in `--help`.
9. `datamimic reference scaffold` now exposes the compact schema and cross-field patterns.
10. Element reference descriptions no longer stop at abbreviations such as `e.g.`.

## Verification commands

```bash
.venv/bin/pytest -q tests_ce/functional_tests/test_cli/test_agent_cli_transport.py
.venv/bin/pytest -q tests_ce/unit_tests/test_authoring \
  tests_ce/functional_tests/test_cli/test_cli.py \
  tests_ce/functional_tests/test_cli/test_agent_cli_transport.py
.venv/bin/ruff check datamimic_ce tests_ce/functional_tests/test_cli/test_agent_cli_transport.py
```

The report separates transport success, executable DSL, and semantic intent. A lint-clean
descriptor alone was never counted as an intent pass.
