# Amendment 189 — demographic run-state ownership

2026-10-10. Decision: Astra, delegated architect. Base: `7e9e897350cdb86b1f7efca1bdc1706fffa898bc`.

RUNTIME-CONTEXTS previously said: “Closed Context/SetupContext hierarchy and
row state.” It now says: “Own the Context/SetupContext hierarchy and row state,
and carry the active demographic profile, sampler, overrides and RNG.”

`DemographicContext` carries existing run state. `DemographicsTask` installs it;
`SetupContext` stores/copies it; entity construction consumes defaults and
derives child RNGs. Domains retains profile loading and sampling policy.
Keep this carrier in Contexts. The shared CE/EE target places run state here;
it does not require an EE demographic placeholder.

Only this aggregate sentence changes. Its module declaration is already
accurate. Source, ownership, APIs, dependencies, selectors, layout, baseline,
historical evidence and decision labels stay unchanged. This accepts the
traced responsibility, not every semantic leaf in Runtime.

Evidence: `contexts/demographic_context.py:11`, `contexts/context.py:332`,
`tasks/setup/demographics_task.py:19` and `tasks/values/construction/entity.py:59`
under `datamimic_ce/engine/runtime/`.

LOCAL VERIFIED: 13 recursive definition checks, Ruff and full MyPy (488 files)
pass. Fresh published ArchKeel 1.1.1 retains exactly the same 13 violations,
254 canonical UNKNOWNs, coverage, source digest and 20 observed record sections.
Only the contract sentence changes.

Native against-base amendment writing exits 2 with 19 `interface.usage_unknown`
diagnostics, nine baseline-new groups, zero resolved groups and one prose-field
widening. It writes no amendment JSON; `amendment_status` is null. This exact
clarification is architect-approved but not machine-bound. The
[receipt](step-188-context-responsibility-receipt.json) retains the failed writer
result and unchanged findings. No baseline or rule is relaxed.
CI-ONLY VERIFICATION: pending for this correction. Full target acceptance remains open.
