# Amendment 60: capability wording and package-version metadata

Date: 2026-09-28. Decision: Astra, under the delegated architecture review.

The frozen and current full capability documents differ at eight paths:

- `elements.{generate,iterate}.attributes.{sourceEntity,targetEntity}.description`:
  four descriptions drop the obsolete `StatementUtil.resolve_source/target_entity` suffix.
- `elements.variable.attributes.type.description`: one description replaces
  the `StatementUtil.resolve_source_entity` reference with the same precedence rule.
- DM401 provenance: `ExporterUtil target parser and ExportOperation enum.` becomes
  `DSL target parser and ExportOperation enum.`
- DM402 provenance: `TaskUtil source dispatch contract.` becomes
  `Source routing contract.`
- `schema_version`: package-version metadata differs.

The field semantics remain unchanged. DM401's intermediate "IO target parser"
wording was inaccurate and is corrected here. Restoring deleted utility names
would publish false ownership.

The eighth path, `schema_version`, is the installed package version from
`importlib.metadata.version("datamimic_ce")`, not the AuthoringSpec schema
version. A difference between separately installed revisions is expected.
Keep both raw documents, hashes and version strings. Only this metadata field
and the seven named wording changes are accepted; no enum, type, required flag,
constraint, rule severity or other description may differ. Missing or invalid
version metadata is not an equivalence proof. Compiler and both reference
projections remain byte-identical. Lint and transport equivalence require
their own evidence.

This is an explicit product-output exception to protocol item 6, not a claim
that the full capability output is byte-identical or that all DSL behavior is
verified.
