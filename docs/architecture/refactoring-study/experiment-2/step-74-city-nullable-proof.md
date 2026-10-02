# Step 74 — Deterministic City nullability proof

The unseeded City descriptor can sample numeric or empty populations. Existing random tests do not guarantee both branches execute.

Added fixed-record unit checks for numeric, empty and `None` populations through `City.to_dict()`, including field presence and exact value type. Malformed numeric input still raises `ValueError`.

LOCAL VERIFIED: changed unit file plus unchanged City descriptor integration test: **7 passed**. Ruff format/check and `git diff --check`: clean. Independent Luna test implementation; controller source review and rerun.

CI-ONLY VERIFICATION: not yet run for this commit.

No production, descriptor, architecture-contract, baseline or comparison-rule changes. This proves nullable conversion, not full descriptor parity. The retained multi-XML artifact/ordering gap and incomplete corpus captures remain open.
