# Amendment 86: IO owns export completion

Astra decision, 2026-10-01; Alex delegated architecture decisions and execution.

Runtime decides when to finalize/publish and traverses statements. IO performs
those operations and removes its run-specific temporary chunks. Move existing
completion functions from registry to `engine/io/exporters/lifecycle.py` and
extract Runtime's existing cleanup loop there. No behavior change or alias.

Declare the three public lifecycle operations, its registry/core dependencies,
one responsibility sentence, and the exact physical target child. No rule,
baseline, type allowance or budget is relaxed.

Eight exporter children are intentional: shared primitives, four output
families, construction, worker page dispatch and completion. Session and
lifecycle independently depend on registry. Another grouping would add no
ownership boundary. The same lifecycle owner is the CE/EE physical target;
EE migration and its current Context dependency require separate verification.

Proof: independent QA before implementation; unchanged file-descriptor
comparison; focused/unit tests, lint/typecheck, definition/cycle checks and
official 0.8.3 report. Results belong in step-86's final record.
