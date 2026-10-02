# Step 91: native Runtime properties

2026-10-02. Base `3f604a3b`; published ArchKeel 0.8.4. Astra approved removal
of the empty PlatformProperties wrapper. Interfaces still adapt callers,
Runtime still sequences execution and DSL still parses/merges properties.

The loader returns its parser map directly. RunRequest carries the same native
map or None to parser and SetupTask. No copy, coercion, new validation, shim or
PlatformConfiguration change. External wrapper consumers remain UNKNOWN under
the approved CE5.0 contraction, not universally compatible.

[Amendment 89](amendment-89.md) permits exactly the loader's string-map return
and create_run_session/run request.platform_props. Empty field_path is the
published top-level selector; the initial absent-key notation was our plan error,
corrected by Astra after checking released schema/parser/matcher.

| Released-checker snapshot | Violations | Counted UNKNOWN |
|---|---:|---:|
| Base | 106 | 157 |
| Source only | 109 | 157 |
| Three exact selectors | 106 | 157 |

All parse492 modules, with no invalid diagnostics. Calls unresolved1269,
typing positions145 and package-roll-up cycle edges2 are unchanged. Digest-bound
amended validation exits1:69 baseline-new facts and measurement drift remain;
the baseline is not refreshed. This is no global architecture PASS.

Independent preflight finds later native request fields despite descriptor_path
UNKNOWN. Wrong property paths restore two findings; an unrelated fixed request
map creates two; an object-valued loader return creates two despite the exact
string-map allowance. No ArchKeel blocker or implementation change is needed.

LOCAL VERIFIED: independent RED10 failures/11passes on base. Candidate standard
plugin Runtime/unchanged DSL properties/process utilities:45passes. Root's
definition7, Pylint executable import-cycle check, Ruff and MyPy492 pass. Full
Make unit suite:1599 passes,11 skips,one existing xfail. These sets overlap.
Astra's independent specification and code-quality reviews pass for this
bounded checkpoint, not the complete architecture or full corpus.

Unchanged oracle inventories930 XML files. Six selections (two seeded, four
unseeded, including property-file/include cases) and four Authoring projections
compare before/after with zero differences or tolerated variances. Historical
capabilities projection drift and full corpus/service parity remain unfinished.
Descriptors, comparator and repository baseline are unchanged.

CI-ONLY VERIFICATION: pending for Step91. Parent3f604a3b CI completed with only
architecture failing; E2E/release skipped. PR274 stays Draft. Physical definition
checks do not certify every semantic leaf, EE parity or complete report usability.
