# Step 84 — enforce mask-character controls

Base: `6739b2159813ecd390c235ba32c3d5a1587f8c11`.

Mask/MiddleMask constructors now require a one-character string before checking length. Valid strings/subclasses, conversion, index behavior, payload rejection and public class identity stay unchanged. Invalid list/bytes/int/None controls now raise ValueError at construction; earlier rejection and changed error type are intentional, not perfect invalid-input compatibility.

Independent Luna implementation and BEFORE/AFTER QA; Astra approved the four-file diff. Real constructors, factory and packaged converter descriptor retain the assessed valid outputs. No descriptor, oracle, architecture contract, allowance, budget or baseline changed. Domain-native payload allowances and CustomConverter context remain unresolved.

LOCAL VERIFIED on the exact combined Step83/84 candidate: 1,569 unit passes, 11 skips, one xfail; Ruff and full MyPy (491 files). Two existing no-port connection-config warnings remain. Pylint executable-cycle, five recursive target and four inner target checks pass.

ArchKeel **0.8.1 release**: unchanged 106 violations / 157 counted UNKNOWN, baseline_new 69. This improves a real runtime invariant; it does not reduce the boundary typing debt. The architecture gate stays FAIL.

QA also found pre-existing MiddleMask index concerns: negative start can duplicate a character; non-integral indexes fail only during conversion; bool indexes are accepted. These behaviors are unchanged and need separate index-policy triage. The new mask-character check does not validate indexes.

CI-ONLY VERIFICATION: no new pipeline inspected yet. Full DSL/EE parity, interactive report acceptance, merge and release remain open.
