# Step 17: Compare unseeded XML output structure

The descriptor oracle now records expanded XML names, attribute names, text
presence, ordered child structure, and element counts. It ignores unseeded text
values. The comparator rejects missing or internally inconsistent evidence;
seeded output still requires the exact digest. No descriptor or runtime code
changed.

Independent implementation and QA passes preceded root review. QA found two
false passes in the first draft: identical malformed XML evidence and boolean
counts accepted as integers. Both are now rejected. The old and current CE
trees capture the previously unverified XML-only descriptor and compare equal.

LOCAL VERIFIED: 52 focused oracle tests, both oracle self-tests, Ruff, and
`git diff --check` passed. The selected XML descriptor is `CAPTURED` in both
trees and equivalent. This proves structure for that case, not identical
unseeded values or the full descriptor corpus.

CI-ONLY VERIFICATION: not run. The full old/new corpus and service-backed
descriptors remain open. ArchKeel 0.8.0 still cannot parse the current
recursive contract; the candidate report is not a released gate.
