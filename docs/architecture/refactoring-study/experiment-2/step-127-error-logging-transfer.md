# Step 127 — error/logging transfer audit

Independent reviews traced CE/EE runtime, Python, CLI and Authoring error
owners. [The receipt](step-127-error-logging-receipt.json) retains their source
scope, first passes and Astra's decision. No EE source or tests changed.

CE retains E002 classification/formatting and legacy `DomainError` behavior.
Runtime owns logging/rethrow; Authoring owns DM002 projection and child-stderr
suppression. These are separate contracts, not exact CE/EE error equivalence.
EE's Redis/runtime configuration and handler transport are not inferred CE
requirements. Amendment18 still defers descriptor-location context.

QA found a concrete duplicate-log path missed in the implementation first pass:
factory validation logs a missing entity before execution logs it again.
[Step 128](step-128-factory-error-logging.md) proves and corrects that path under
[Amendment163](amendment-163-factory-error-log-ownership.md).

The audit does not close all required transfers, establish a global log-once
policy or prove exact stream/traceback parity. Broader acceptance remains open.

LOCAL VERIFIED: independent source/caller/test-owner review. No EE runtime tests
or services ran. CI-ONLY VERIFICATION: none added by this audit.
