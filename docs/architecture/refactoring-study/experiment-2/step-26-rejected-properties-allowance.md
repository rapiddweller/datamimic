# Step 26 candidate: top-level property allowances not expressible

Astra selected three open `dict[str, str]` property returns for exact
`boundary_types` allowances. The DSL parser accepts caller-defined keys;
IO's file reader forwards it and the profile loader selects its location.
Narrowing these to fixed DTOs would misstate their contracts.

The candidate added exact `allowed_positions` to `DSL-API-TYPES` and
`IO-API-TYPES`, but ArchKeel 0.8.1.dev20 rejected the contract before scanning:
`allowed_positions[0] fields mismatch`. Its schema requires a nonempty
`field_path`, and the matcher handles only nested paths, not a top-level
`return dict[str, str]`. No `allowed_sources` or whole-facade exemption was
substituted. The invalid amendment was removed, and Step 24 remains the
accepted contract and report (119 violations, 237 UNKNOWN positions).
ArchKeel [#207](https://github.com/rapiddweller/archkeel/issues/207) tracks
the missing exact top-level allowance.

LOCAL VERIFIED: existing properties tests passed in independent QA (19),
the parse-error report, ArchKeel codec/matcher inspection, and clean contract
reversal diff. A full descriptor inventory and CI were not run.

CI-ONLY VERIFICATION: not run.
