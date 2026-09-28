# Amendment 29: expose the DSL leaves IO actually consumes

Date: 2026-09-28. The 12 IO→DSL imports used the broad `dsl.api` facade.

IO now imports the owning vocabulary and input-parser modules. Declare only
the observed symbols public and permit those module paths in IO's `requires`.
The parser functions and DTD error retain their existing implementation;
no compatibility forwarding module or descriptor changes.

This is a narrow interface widening for existing IO callers, not a new
external Python API. Independent review confirmed fresh-process imports,
DTD rejection, and no new IO↔DSL cycle. The root `REQUIRES-COMPLETE` rule now
passes; the full architecture gate remains red for other findings.

LOCAL VERIFIED: 138 focused tests by implementation, 78 by independent QA,
the 1948-test non-service suite, Ruff, Mypy, recursive definition check,
and Pylint import-cycle check. The frozen oracle inventoried all 930 XML
descriptors; comparison to the prior slice differs only in two unseeded
cases that vary on same-code repeat. Its exit remains 1 because the original
frozen capabilities hash already drifted in earlier slices.

CI-ONLY VERIFICATION: no remote run.
