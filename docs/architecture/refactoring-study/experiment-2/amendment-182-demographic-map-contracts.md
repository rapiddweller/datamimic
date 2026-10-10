# Amendment 182 — demographic maps inside typed records

2026-10-10. Decision: Astra, delegated architect. Base `3d31ed4f`.

SHARED-DEMOGRAPHICS owns configuration, profile validation and sampling. Its
existing records have fixed typed fields; the maps inside them use data keys:
profile weight names, sex buckets and condition names. Runtime owns installation
and access to `DemographicContext` and reuses those Domain records.

Amendment 70 already accepted a profile name, weight mapping or None at three
Runtime positions. Replace their incomplete `Mapping[str, float]` selectors
with the complete union below. Additionally grant the seven Domain positions,
superseding Amendment 73's map hold and the corresponding DTO feature hold in
176/178 only for these fields. Earlier amendments did not grant these seven.

All selectors omit `container_depth`; none accepts object opacity. Prefixes
are `datamimic_ce.domains.api.` and `datamimic_ce.engine.runtime.api.`.

| Rule / qualified suffix | Position | Field path | Complete annotation |
| --- | --- | --- | --- |
| Domain / `DemographicConfig.with_defaults` | return | transaction_profile | `str \| Mapping[str, float] \| None` |
| Domain / `PersonService.__init__` | demographic_config | transaction_profile | `str \| Mapping[str, float] \| None` |
| Domain / `PatientService.__init__` | demographic_config | transaction_profile | `str \| Mapping[str, float] \| None` |
| Runtime / `SetupContext.__init__` | demographic_context | overrides.transaction_profile | `str \| Mapping[str, float] \| None` |
| Runtime / `SetupContext.demographic_context` | return | overrides.transaction_profile | `str \| Mapping[str, float] \| None` |
| Runtime / `SetupContext.set_demographic_context` | context | overrides.transaction_profile | `str \| Mapping[str, float] \| None` |
| Domain / `load_demographic_profile` | return | age_bands | `Mapping[SexKey, tuple[DemographicAgeBand, ...]]` |
| Domain / `load_demographic_profile` | return | condition_rates | `Mapping[str, tuple[DemographicConditionRate, ...]]` |
| Domain / `DemographicSampler.__init__` | profile | age_bands | `Mapping[SexKey, tuple[DemographicAgeBand, ...]]` |
| Domain / `DemographicSampler.__init__` | profile | condition_rates | `Mapping[str, tuple[DemographicConditionRate, ...]]` |

Keep Domain's other 25 selectors and Runtime's other 32 selectors unchanged;
totals become 32 and 35. Both rules remain agent-decided. Fixed fields, map
keys and concrete value records still require precise types.

`with_defaults` creates a new config while retaining the transaction mapping.
Services/entities pass that value through; this does not promise automatic
Finance weighting or JSON support for arbitrary Mapping implementations.
Runtime installation/getter/setter retain the context; SetupContext deepcopy
still copies it. Loaded profiles use sorted tuples of typed records, normalized
open sex keys and a None fallback. Sampler weight indexes remain snapshots;
no new promise is made about later map mutations updating them.

No production, EE, ownership, public/dependency, baseline or oracle changes.
GroupMask aliases, Properties, raw CSV and malformed-input contracts, and SQL
remain separate open work. Expected delta: only these ten map findings disappear,
37 → 27; Domain 10 → 3 and Runtime 8 → 5. Preserve all remaining findings,
254 canonical / 200 measured UNKNOWNs, source facts and 151 components / 25 levels.
Evidence: `/tmp/ce-resume-20261010/next-slice-167/`.

LOCAL VERIFIED: 18 behavior characterizations pass before the contract changes;
both exact contract guards fail. With the same five test files, all 114 selected
ownership, Runtime, service/schema, loader, sampling, override and constructor
tests then pass. Definition checks: 13 PASS; package Ruff, full MyPy (488 files)
and Ruff for the changed tests: PASS. Production source is unchanged.

Fresh ArchKeel 1.1.0 report: FAIL27, Domain3 / Runtime5, 200 measured UNKNOWNs,
488/488 parsed files. Independent prechecks pass 92 matcher counterexamples and
four source-fixture variants covering fixed fields and map key/value widening.
The independent comparison preserves all 27 remaining findings and 254 canonical
UNKNOWNs exactly, with unchanged source facts and 151 components / 25 levels.
Ten new allowance facts introduce no accepted opacity.

Native amendment validation retains both Domain/Runtime widenings but exits 2
with the same 19 usage-UNKNOWN diagnostics and 16 baseline-new groups. No
amendment artifact is emitted; machine binding remains open.
CI-ONLY VERIFICATION: new-head checks pending. No full DSL/EE acceptance.
