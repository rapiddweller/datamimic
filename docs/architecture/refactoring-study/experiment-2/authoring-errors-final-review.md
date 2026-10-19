# CE Authoring and Errors final architecture review

**Accepted within the local architecture review scope. No remaining actionable branch finding.** Reviewer: Astra. This is not merge authorization, a whole-system correctness certificate, or a native all-PASS claim.

## Binding and approved policy

Review covers development `dd2e0ee20cf43b1dfd9a8eda4986345025de3a8e` through HEAD `05d9b905eac9f6a5df2e6d9ae99a340abfd528d7`, plus the explicitly approved two-value baseline amendment.

- Source: `5f22f036f4494462acb508e4817cf8934c4f371a21c609296361580edd701203`, bounded to `datamimic_ce/**/*.py`.
- Target: `8517a10b1fd874b2e66f7161044074d8ff649639a9f8e37e17f92c2456cc0d85`.
- Analyzer: `bb1a3262d3fdd38c3e9a6af980cc063281ae98ab1c28c89c2c5be6dfb450744f`; package ArchKeel 4.0.1, Python 3.11.12.
- Canonical validation digest: `622bbfad0d349e71e341a4df1792a9070fd04ece58a8d246a1b667e7a35f8f31`.
- Direct user acceptance authorizes **only** `calls_unresolved: 1409 → 1425` and `typing_positions: 173 → 178`. Other budgets, contracts and strict completion checks remain unchanged. The change acknowledges residual measured uncertainty; it does not resolve it.

Independent hashing confirms that only `known-violations.json` differs among the 2,070 frozen product/policy files. All 1,723 installed-wheel package files, including 534 Python files, still match. Archived native report provenance retains its original Git head/dirty state; exact file binding, rather than relabelling that historical metadata, establishes applicability to this candidate.

## Connected whole-branch review

The supplied implementation plan, current AGENTS, migration contract, recursive target inventory and whole-branch change inventory were reviewed. Existing source-bound independent evidence was reused for unchanged paths; this review does not pretend to reread every line or rerun all suites.

- Public Python/CLI/MCP enter one Authoring application. Bootstrap selects CE adapters; named ports separate orchestration from codec, catalog, parser, workspace and execution ownership. Application does not import adapters.
- Transient `DmJsonDocumentV1` and transaction-scoped `BuildRequestV4` replace the active Intent/Scaffold workflow. XML remains persisted runtime input. The isolated migration script reads the frozen legacy compiler, preserves proof declarations and exposes unsupported cases rather than installing a second active compiler.
- Build compiles and validates, projects mandatory acceptance, captures bounded execution, evaluates complete rows, then produces response samples. Requested smoke and replay remain separate gates; replay compares complete typed values. Partial, dynamic/unknown or missing capture cannot acquire Ready through sampling or a passing optional gate.
- Connected fixes retain dynamic-count uncertainty, recursive value identity, descriptor-relative workspace containment, runtime target-entity precedence, conditional field multiplicity and mandatory memstore readback. The Counter operation enforces an actual invariant; no wrapper or annotation workaround is needed to alter static counts.
- CE parser/runtime/IO remain their own owners. The scoped resource-reader port and bounded workspace process preserve contained resource handling without claiming arbitrary descriptor Python is sandboxed. Native client/vendor classification stays with IO.
- Errors owns identity, catalog and factory formatting. Runtime callers preserve typed facts and chained native causes. Script/generator descriptor context is inserted once by its factory; no rendered-cause matching selects guidance. Domain metadata and edition-specific semantics remain intact.
- Python >=3.11, CE SCM versioning, optional MCP and DTO-derived schemas remain consistent with the migration. No active old compiler, EE/Redis/Torch dependency, new shared library or unrelated architecture layer was found in the reviewed authoring/errors paths.

The seven-finding repair review, conditional field review, descriptor-context review and portable-contract mutation review remain applicable. Their source binding and current implementation agree; no valid finding is left open. Existing large Domain/adapter/catalog leaves retain cohesive named owners documented in the recursive inventory; a new grouping layer would not remove a responsibility.

## Native result and retained uncertainty

Fresh approved validation differs from the previous 4.0.1 validation **only** in `failures`, now empty. Coverage is 534/534 full AST, zero reported violations, zero baseline additions/resolutions. Native rules remain **271 PASS and 5 UNKNOWN**. Native validation still exits 2 for the same 20 `interface.usage_unknown` diagnostics; the full report exits 0. These facts are compatible with the strict gate's explicitly assessed uncertainty path.

All 303 raw UNKNOWN records and all 20 raw diagnostics are unchanged and retained. The receipt assigns every UNKNOWN exactly once across 12 classifications:

- Four public API surfaces; seven DSL reexport routes; six overlapping boundary aggregates.
- 284 boundary positions: 130 inherited, 74 other/property/alias, 50 external, 12 generic, eight dotted, five forward reference and five missing annotations.
- One context-alias aggregate and one dynamic-call aggregate at 1,425 unresolved calls.

Missing annotations and broad/opaque shapes remain source-contract debt where reported; they are not all called analyzer limitations. The five UNKNOWN rules remain AUTHORING-, DOMAIN-, DSL-, IO- and RUNTIME-API-TYPES. Passing runtime tests or MyPy does not resolve them.

The 20 exact diagnostics cover CompiledDocumentArtifact and 15 Domain symbols across 19 Domain publication routes. Four symbols published at additional distinct pointers are retained. No used/unused inference, deletion permission or native PASS is granted. Full raw records and per-diagnostic assessments accompany the external review evidence.

## Verification boundary

**LOCAL VERIFIED independently:** connected source review, exact approved-policy diff, 2,070-file product/policy comparison, 1,723-file wheel-source comparison, validation delta, raw UNKNOWN/diagnostic equality, strict completion-gate acceptance of all 303 UNKNOWNs and six rejecting mutation controls (changed validation, omitted/duplicated UNKNOWN, omitted diagnostic, wrong analyzer, remaining budget failure). No collector or product suite was duplicated.

**LOCAL VERIFIED through reviewed existing evidence:** independent repair regressions, conditional controls, context matrices and negative factory-contract mutations; final installed wheel 48 regressions, 118 functional tests and three installed profiles; 13 schemas, 11 MCP tools and 173 resources agree. The earlier unit evidence is composed 2,975 passing identities plus 15 existing skips, **not one clean full run**. The parent owns the fresh full-unit result and later delivery checks.

**CI-ONLY VERIFICATION:** final exact-head CE CI and applicable Windows/service execution are not established by this review. No CE merge, release or deployment is approved here. EE delivery evidence is separately owned and was not rerun.

Skipped: duplicate broad suites/collectors and a new whole-EE audit. Residual risk is the explicitly retained native uncertainty and any outstanding final-head CI; receipt acceptance does not close either by implication.
