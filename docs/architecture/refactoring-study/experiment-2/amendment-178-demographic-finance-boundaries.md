# Amendment 178 — demographic maps and optional account hint

2026-10-09. Decision: Astra, delegated architect. Base `17c26b2fa748b6919cf012eef6e510097163e5d3`.

Approve five exact direct positions in DOMAIN-API-TYPES, independently reviewed:

- DemographicSampler's `age_band_weights`, `condition_weights` and `sex_weights`
  returns are fresh, precisely typed maps with dataset-defined keys.
- `apply_profile_groups.profile_row` accepts a read-only string/None metadata map;
  it reads known group-reference keys and returns the same sampler.
- `TransactionGenerator.generate_transaction_data.bank_account: object | None`
  is an optional currency hint. Existing truthiness and CurrencyAccount checks
  select account currency; other inputs retain generated-currency fallback.

These two policy decisions supersede only Step125's holds on these five positions.
All 20 prior Domain allowances remain. No wildcard, nested DTO or container-depth
permission is added. GroupMask, precise finance output and unrelated signatures
remain constrained. Domain's agent attribution is unchanged.

The demographic input contract does not certify malformed CSV producers. Raw
DictReader rows still contradict their narrow annotations; overflow can fail in
profile_group_refs before apply_profile_groups is called. The physical CSV move
remains held. Opaque finance input does not guarantee success for every object;
native truthiness, protocol and property errors remain observable.

Product source, ownership, public/dependency grants, baseline and oracle are
unchanged. The existing exact Runtime contract test is synchronized with
Amendment176's RegisteredClient and source-length positions; its set comparison,
duplicate rejection and wildcard guard remain intact. The missed expectation
caused both Step157 CI unit jobs to fail and was reproduced locally before repair.

LOCAL VERIFIED: five exact matcher positives/84 negatives, definition 13,
Runtime boundary tests 62 and full unit suite 2,307 passed (11 skipped, one
expected failure). Changed-test Ruff passed; Step157's source lint/MyPy and
inner/cycle evidence are reused with identical product source/dependencies.
The integrated report removes exactly these five findings: FAIL58 / 200 measured
/ 254 canonical UNKNOWN. Every remaining finding/UNKNOWN record is exact;
151 components, 25 levels, zero ownership gaps and all structural fields remain.
Source digest remains `49fc0d9b223dfc1e0eb69e3745929e7ea1aac43703125c053bc8046b7b81c0f3`.

Baseline/against-17c validation exits 2: 32 new/zero resolved baseline entries,
19 usage-UNKNOWN diagnostics and one approved allowed_positions widening.
Amendment binding remains unproven (ArchKeel #415); the baseline is unchanged.
Receipts: `/tmp/ce-resume-20261008/next-slice-158/`.

CI-ONLY VERIFICATION: pending for this commit. Both Step157 CI runs finished
with the missed exact-contract test and two architecture jobs failing; all other
executed jobs passed. Full DSL/EE compatibility, machine-bound amendments,
evaluated UNKNOWNs and full target/responsibility acceptance remain open.
