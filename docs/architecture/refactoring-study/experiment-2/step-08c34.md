# Step 08C34: Authoring uses the IO count boundary

The bounded dry-run used `DataSourceRegistry._get_source` to read every file row
just to count it. It now calls IO's existing `count_source` operation. The
file-only and DBUnit exclusions, failed-probe `UNKNOWN`, separator, and offset
behavior remain unchanged. No descriptor or exporter implementation changed.

Independent QA passed 40 focused Authoring tests and checked separator, offset,
and DBUnit cases. The broader Authoring and descriptor-oracle suite passed
485 tests; recursive target-definition tests passed 5/5; Pylint found no cyclic
imports. The implementation pass also passed Ruff and full-package MyPy.

This removes one private cross-component call. It does not certify the full
target: the local ArchKeel candidate still reports contract-invalid public
declarations and boundary findings, which need separate review.
Before and after this slice, report mode shows 125 violations and 251 unknown
positions. ArchKeel does not currently count this private method reach-through;
the unchanged totals are not evidence that the boundary was already sound.
