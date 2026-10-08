# CI architecture reviews

CI builds reports with the published ArchKeel **1.0.0** wheel. Report generation
is independent of the architecture gate. Publishing a report does not mean PASS;
the native validation receipt retains FAIL and UNKNOWN.

- [Report history](https://rapiddweller.github.io/datamimic/)
- [PR #274 latest review](https://rapiddweller.github.io/datamimic/pr/274/)
- Each run: `runs/<run-id>/<attempt>/` with HTML, JSON, full detail and provenance.
- CI also uploads `architecture-report-<attempt>` as downloadable evidence.

The trusted `development` publisher never executes PR scripts. It accepts only
five report files from completed, same-repository CI runs. Fork runs retain
read-only artifacts but do not publish active HTML on the shared Pages origin.
PR scans may use a GitHub merge ref: head SHA and scanned SHA are shown separately.
This provenance is not an independent attestation of the scanner execution.

`architecture-reports` retains all original evidence. One serialized workflow
appends and deploys it. A stale head or older attempt cannot replace a newer PR review.
Pages hosts full details for the current run and each open PR's latest review.
Historical interactive diagrams remain online; their JSON and full-detail HTML
are clearly labeled downloads from the unchanged Git archive. This avoids copying
about 37 MiB into Pages for every CE run. Publication fails visibly if the Pages
projection exceeds 900 MiB; original evidence is never silently deleted.
The Git archive still grows with every run. Git compression does not shrink its
checkout; repository and runner disk limits remain an operational ceiling.

Bootstrap lands the publisher separately from the CE refactoring. Branches without
a report job are explicitly marked **not published**, not architecture PASS.
If a report job ran but its artifact is missing or invalid, publication fails.
Use a full rerun to create a new report; retrying only failed jobs may not rerun
an already successful report job. The old attempt remains available unchanged.
