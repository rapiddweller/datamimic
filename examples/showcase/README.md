# DATAMIMIC showcase gallery

Five self-contained, runnable examples. Each descriptor is seeded: running it
twice produces the identical dataset. Each README states the exact run command
and the semantic rules the example demonstrates. All five are executed and
verified by CI (`tests_ce/unit_tests/test_showcase/`).

| Example | Question it answers |
|---|---|
| [01-banking-core](01-banking-core/) | How do I generate a multi-table banking dataset with referential integrity? |
| [02-multi-source-assembly](02-multi-source-assembly/) | How do I assemble one dataset from a CSV, generated fields, and a lookup table? |
| [03-orchestration-timeseries](03-orchestration-timeseries/) | How do I branch records conditionally and generate evolving time-series data? |
| [04-python-seam](04-python-seam/) | How do I extend the DSL with custom python generators and converters? |
| [05-dsl-power](05-dsl-power/) | How do I export one dataset to five formats, generate BLOBs, and enforce per-record invariants? |

Start with 01; it is the pattern the other three build on. The DSL reference
lives one tool call away: `datamimic_reference topic=overview` (MCP) or
`datamimic capabilities` (CLI JSON manifest). Lint any descriptor with
`datamimic lint <path>`; every finding carries a rule id and a fix hint.
