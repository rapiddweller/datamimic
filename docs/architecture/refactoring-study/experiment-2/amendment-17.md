# Amendment 17: group the CLI under interfaces

Date: 2026-09-24.

The frozen target moved CLI below `interfaces/` but did not constrain its internal layout. Four
command modules at that level still made the transport boundary hard to scan. Keep the same
`interfaces` component and public `datamimic_ce.interfaces.cli:app` entry, but place the CLI
implementation in `interfaces/cli/`. Add one nested `root_layout` rule so the grouping cannot
silently drift back. This narrows the target; it grants no new component dependency.

Acceptance: the console script, `python -m datamimic_ce.interfaces.cli`, and their success and
usage-error paths work; descriptor and authoring projections do not change.
