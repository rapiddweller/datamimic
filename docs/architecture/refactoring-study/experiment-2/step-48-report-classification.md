# Step 48: correct report classification

The ArchKeel candidate now treats an exact declared module target as covered,
even when it intentionally sits outside component ownership. The CE root and
engine initializers therefore remain visible in Actual and Target, but no longer
appear as false "Unmapped" Diff entries. Breadcrumb and Back navigation also
clear a stale responsibility selection. Analyzer facts and the 95 rule
violations did not change.
The artifact contains 491 observed Python modules and 491 exact module targets:
no observed file lacks a target and no declared target file is absent. Its HTML
explorer payload also contains all 491 Actual and all 491 Target module nodes.

The 189 counted UNKNOWN positions are not one homogeneous CE typing backlog:

| Cause | Count | Current disposition |
| --- | ---: | --- |
| Missing annotation | 52 | Review CE code and type only real boundaries. |
| Inherited surface | 65 | ArchKeel cannot yet inspect the inherited facade surface. |
| Ambiguous facade or unresolved route | 17 | Check alias resolution; do not call these PASS. |
| Generic, dotted/forward/unresolved name, other | 55 | Review each position against its owner and intended API. |

Another 67 `external_type` positions are neutral because their owners are
outside the declared components. Six aggregate records and two standing
analyzer disclaimers appear in the raw 264 UNKNOWN records but are not extra
positions. These are classifications, not resolutions.

The local ArchKeel fix is commit `b8f9852` on
`feat/inherited-generic-facade-types`; it is not a released 0.8.0 fix. The
regenerated CE report is
`test-artifacts/architecture/ce-current-step50-report-correction/architecture.report.html`.

LOCAL VERIFIED: ArchKeel format, Ruff, MyPy, self-observation and 2,081 tests
passed. Three environment-specific tests were deselected: two non-UTF-8 path
tests unsupported by this macOS filesystem, and one isolated Python 3.12 run
that could not reach PyPI. Playwright inspected the real CE report: both
initializers appear in Actual and Target, Diff has no false Unmapped entry,
and Back clears the prior responsibility. ArchKeel self-validation exits zero
with 0 violations, but `declared_rules=UNKNOWN` (48 UNKNOWN positions), not PASS.

CI-ONLY VERIFICATION: not run. The CE descriptor oracle was not rerun because
this step changes only report rendering; the CE source remains dirty from
earlier refactoring steps.
