# Amendment 176 — native map boundaries

2026-10-09. Decision: Astra, delegated architect. Base `184e1edbd6a2fff0185fa32878a78831470d400b`.

Runtime owns client-ID registries and cached counts keyed by statement/source
identity. IO owns weighted CSV rows keyed by dataset headers. These are dynamic
data keys, not fixed execution-control fields. Wrappers add no invariant and
would change exposed dictionary identity.

Approve only these direct, empty-field-path selectors in the root contract:

- RUNTIME-API-TYPES: reconcile the three existing client constructor/getter/setter
  annotations from `Client` to `RegisteredClient`, preserving structural SQL
  clients under Amendment155.
- RUNTIME-API-TYPES: constructor `data_source_len` and getter return, with their
  exact `dict[tuple[str | None, str | None], int]` annotations and existing
  constructor optionality. This supersedes Amendment95's debt disposition only
  for those two positions.
- IO-API-TYPES: `WeightedEntityDataSource.generate` returning `dict[str, str]`.
  Preserve selected-row identity, weight handling, RNG draws and native errors.

Both amended rules become agent-decided; attribution is rule-wide because the
schema has no per-position attribution. No source, ownership, public/dependency
grant, baseline or oracle changes. No DTO-field/container-depth permission is
added; Alex's feature deferment remains binding. Getter/setter resolution and
unrelated UNKNOWNs remain unproved. This corrects the target, not runtime code.

LOCAL VERIFIED (combined with Amendment177): 23 exact matcher positives and
83 negative controls; Ruff, full MyPy (488 files), 13 definition tests. Published
ArchKeel 1.0.0 removes exactly the 23 approved findings: declared FAIL63,
200 measured/254 canonical UNKNOWN. All remaining violations and UNKNOWNs are
exact; source/modules/dependencies are unchanged. The projection retains all
151 components, 25 levels and zero gaps. Existing typing facts change only by
inheriting this amendment's provenance (10 records); 23 allowance facts are added.

Baseline plus unamended against-base validation exits 2: 37 new, zero resolved,
19 diagnostics, 67 failures and five unbound widenings across the three rules.
Amendment status stays null; machine binding remains open (ArchKeel #415).
Initial sandbox commands stopped at uv cache access before executing checks;
the authorized cache-access run produced the results above. One initial matcher
input comparison also failed before matching; corrected shape comparison passed.
CI-ONLY VERIFICATION: pending for the new commit; no CI success claimed.
