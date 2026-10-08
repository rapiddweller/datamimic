# Step 116: isolate property-binding uncertainty

Independent Luna probes; root replays with published ArchKeel **1.0.0**.
No CE/checker/contract/oracle/baseline changes. Source digest remains
`d5fdc6789839b6dabade4917eb545f6f9aa5bf0b82e71baca46f89c0be3625d6`.

QA's explicitly selected getter/setter and inherited-getter/child-setter forms
report PASS. The separate implementation getter-only fixture reports PASS with
zero evaluated positions; that status is not getter-annotation proof.
Adding one uncalled `exec` function to the QA fixture produces five UNKNOWN
positions while retaining declared annotations. This matches the intended
uncertainty retention in [ArchKeel #306](https://github.com/rapiddweller/archkeel/issues/306),
not missing ordinary setter support or evidence loss.

A separate integer-property fixture isolates another shape:

| Single-property fixture | Rules | Violations | UNKNOWN | Validate exit |
|---|---|---:|---:|---:|
| Setter `value(self, value: int)` | UNKNOWN | 0 | 4 | 0 |
| Only parameter/RHS renamed to `new_value` | PASS | 0 | 0 | 0 |
| Renamed case; only getter return changed to `object` | FAIL | 1 | 0 | 2 |

The two-line rename changes `source_member_binding_static` from false to true.
Contract bytes, getter, counters and property membership remain identical.
Counter removal, class selection and module-location controls do not change
the original four UNKNOWNs; an invalid selector attempt is excluded.
The broad-return negative control proves the positive getter is evaluated.
`typing_positions=0` alone would not prove that. Both ordinary variants retain
identical descriptor-assignment/read/write traces. Direct keyword calls to
`property.fset` have different parameter names; no CE rename is approved.

The 69 CE property positions map to 23 setter chains. Exactly one has the
same-name parameter pattern: `CompositeStatement.sub_statements` in
`engine/dsl/statements/base/composite_statement.py:25`, covering three records.
This is a syntactic candidate subset, **not proof that three CE UNKNOWNs would
disappear**. Its ancestry/other binding limits may coexist. The other 66
positions, including `rng` and `default_dataset`, are not explained by this
collision. Dictionary and inherited-surface debt remain open.

LOCAL VERIFIED: valid original/renamed fixtures, exact source/contract diff,
native descriptor traces, published report/validate results and the required
broad-return rejection; canonical-to-source mapping of all 69 positions.
Evidence: `/tmp/ce-resume-20261008/{property-repro,property-repro-qa,property-diffs-qa}/`.
The collision has a local issue draft; no public issue or source workaround.

CI-ONLY VERIFICATION: none added for these disposable fixtures. Step 115's
remote receipt applies to source checkpoint `9dc1961a`. CE remains **89
violations / 200 measured UNKNOWNs / two cycle edges**; overall acceptance open.
