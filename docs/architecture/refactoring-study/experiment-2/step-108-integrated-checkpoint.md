# Step 108: save and integrate the local experiment

Local checkpoint `0edf29a6` contains the previously uncommitted source, tests,
contracts and review history. It is merged with PR head `5b6bfa49`, preserving
remote-only work. ArchKeel is pinned to the published **1.0.0** release.
Generated reports and browser captures remain local; no source work is omitted.

## Integration decisions

- Keep the remote exact dictionary validation annotations, not the optional
  TypeVar refinement that added eight UNKNOWNs. Runtime mapping behavior remains;
  generic static return preservation is deferred.
- Preserve the intentional CE5 raw Memstore API change. IO applies paging and
  copy policy; external Python callers of the removed arguments need migration.
- Preserve injected SQL capability and native errors. The existing SQL cast
  remains disclosed typing debt, not proof of a closed boundary.
- Amendment 159 supersedes only Amendment 97's exporter-marker assignment.
  Registry owns the exact initializer; descendant owners and permissions stay.

Luna resolves source/test conflicts; independent QA and Astra review catch a
duplicate API export, overlapping initializer owners and four stale test
expectations. The fixes retain exact permission, bool-normalization, paging,
identity and deep-copy assertions. Domain source matches the local parent;
remote tests remain except the intentionally replaced concrete-RDBMS rejection.

## Verification

LOCAL VERIFIED: **2,237 units passed, 11 skipped, one existing xfail**; two
Pydantic serializer warnings. Source/changed-test Ruff, full MyPy (492 files),
33 focused ownership/IO/raw-XML integration tests, pinned Pylint, eight recursive
definition checks and four inner-target checks pass. Diff checks pass.

ArchKeel 1.0.0 reads/parses **492/492** files, AST coverage **100%**.
The strict architecture gate remains **FAIL: 91 violations, 202 measured UNKNOWN
positions, baseline-new 60, resolved 0**. Two package/type-cycle edges remain;
Pylint's executable-import result does not establish zero measured cycles.

No descriptors, intent inputs, oracle, baseline or CI workflows change relative
to either integration parent. Full seeded/unseeded and service-backed final
acceptance remain open. Actual/Target/Diff deep-navigation acceptance is not
established by structural tests. This is a red Draft checkpoint, not TARGET_REACHED.

CI-ONLY VERIFICATION: no passing result claimed before remote execution.
