# Global Build row budget: independent architecture review

**APPROVE the decided budget slice and coordinated catalog reservation.** Reviewer: Astra, 2026-10-21.

CE base `f820c34a768d0f3869af0788077e9f7574152321`, reviewed head `20aba7132b9a79f581c2b51535d2987e7e7cae57`. This continues the approved implementation at `05c18db3b6e1fcda64df8ee138514665e86447e0`. EE companion remains `d9e9cb8b721cc4e37b44060a11632a4374cdeef2` (base `ad3006240d64fc6e8bce1ef5364566e3f8018177`). Prior [Build includes review](issue-356-build-includes-review.md) and its UNKNOWN assessments remain in force.

## Ownership and types

- `RunRequest.total_row_limit` carries the integer control to the root `SetupContext`; its `TotalRowBudget` is shared across includes and nested rows. Removing SetupTask's duplicate memo entry preserves the context-owned deepcopy sharing.
- Runtime declares exactly `contexts.products:TotalRowBudget`. No `api.__all__` export, new owner, Authoring-to-private-Runtime import or broad map permission is added. Inner Target and structure review agree with the source.
- The four exact `RUNTIME-API-TYPES` positions retain `int | None` and `TotalRowBudget | None`. Source review confirms the mutable budget's complete authored state is `limit: int`, `used: int`, with typed `reserve()`/`release()` methods. Mutation is required for the shared counter. No casts, reflection, string dispatch or opaque payload are used.
- Native class inventory remains partial for dataclass-generated behavior; this review does not turn that limitation into full inventory proof. Existing Runtime UNKNOWNs remain: 143 positions, 75 decided, 68 undecided.

## Independent native evidence

Collected the clean exact head with cached ArchKeel 4.0.1, Python 3.11.12, using the Makefile's validation/report commands. No installation was performed.

| Binding | Digest |
|---|---|
| Source | `453df0533ddd44703fb2a0825ddd5f378f61673e9e8a4817bc7358d907ed74d6` |
| Target | `3bc0097467081f6c1c5c96e9bdc8dc85b1bd4de77b7cabd0cbe4848779d80ba6` |
| Analyzer | `bb1a3262d3fdd38c3e9a6af980cc063281ae98ab1c28c89c2c5be6dfb450744f` |
| Validation | `39b0e1397dccf1908e496b85e9a7ad8eb72d55cbcf27f875752b676e76f34001` |
| UNKNOWN | `ea1e034dbebff848066aa035eff3e1f2bf992d456c158246988ba0c636d8ca7e` |

534/534 files, no observation failures, zero violations and zero baseline drift. Rules: 271 PASS, 5 UNKNOWN. All 314 UNKNOWN identities retain their previous assessment categories; the 20 `interface.usage_unknown` diagnostics are byte-for-byte equal as decoded JSON. Measurements remain `calls_unresolved=1426`, `typing_positions=178`, `unknown_positions=256`; private crossings remain zero. No ceiling, baseline, evaluator or completion-gate change is authorized or made. The review receipt changes its binding and adds this assessment, preserving its history.

## Runtime evidence and launcher correction

**LOCAL VERIFIED:** Pinned Pylint 3.3.7 executable-cycle check passed; 40 architecture definition/inner/completion tests passed; the strict completion gate accepted 314 assessed UNKNOWNs. All Makefile architecture gate stages were exercised using existing cached tools. 73 focused tests passed: global budget 7, Runtime boundary 63, independent EOF/replay probes 3. Actual module receipts confirm the candidate in the parent and bounded children. Real independent Builds also pass nested public-limit, time-series (including zero), deep nesting, conditional UNKNOWN, finite-source CAPPED/EXHAUSTED and nested-include overflow cases. Replay and smoke verify fresh equal budgets for the same bounded logical dataset.

The reported three failures were reproduced with a guarded launcher that places the candidate on the parent's `sys.path` but omits it from inherited `PYTHONPATH`. The parent then imports the candidate and bounded children import the primary CE checkout; this reproduces exactly 3 failures / 4 passes and invalid-capture serialization. With candidate `PYTHONPATH` propagated, all seven pass. Restoring two runtime files was not a valid baseline control; these failures do not establish an inherited product defect.

**CI-ONLY / UNKNOWN:** remote CI, full product/service suites, Windows and general EE semantic parity were not established. Earlier worker full Authoring results remain supplied evidence. Other EE issue 2 requirements and V5 project snapshot/digest binding remain open. This approval does not close issue 2 or authorize merge/release.
