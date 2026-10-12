# Runtime session intent

Astra decision, 2026-10-11. Runtime owns descriptor execution; Python entry points consume a runtime-owned session, rather than its task or IO implementation. This applies Amendment20 and the semantic target decision's Runtime/Interfaces responsibilities to the concrete port identified in the accepted CE release scope.

RunSession and RuntimeRunSession must each expose public instance methods `execute(self) -> RunResult` and `capture_test_result(self) -> dict[str, list[object]] | None`. Execution returns the runtime result. Test capture retains native product-column lists and rejects non-test use. Ownership, values and errors are unchanged.

The independent intent asserts those four signatures, not all internals. It does not assert nominal inheritance or a `realization` edge: RuntimeRunSession implements the port structurally. Matching both signatures is necessary evidence for the intended two-operation boundary, not general Python Protocol/subtyping proof. Dynamic binding or incomplete member evidence remains UNKNOWN. No closed member inventory is declared.

Design references: `docs/architecture/refactoring-study/experiment-2/amendment-20.md`; `docs/architecture/inner/semantic-review/astra-target-decision.md` (Interfaces, Runtime ownership, behavioral preservation); `docs/architecture/refactoring-study/experiment-2/amendment-180-runtime-capture-selectors.md` (native capture contract). Existing callers confirm the need: interfaces/python/datamimic.py delegates execution/capture; data_mimic_test.py gates test capture; factory.py executes then consumes captures. These callers select useful obligations; they are not a generated Source-to-Target oracle.
