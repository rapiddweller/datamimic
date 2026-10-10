# Step 177 — ArchKeel 1.1.1 report navigation

Independent QA inspected the published 1.1.1 report at CE head `019f9cbc`
and source digest `c9e1c15f0095ce63f40e7cebb193b06e091fc483e3d52870f94f0aea2f0f783c`.
The report JSON SHA-256 is `7a69f16e32839a814ab7f69822baab1d62a0297e1ce17140d03f4e78553a1911`;
the main and detail HTML hashes are `c8e78b1586154cf9f906ac0f4f84fc83b0278106c5cebd1cf6c986c0ca170d60`
and `48c71f6e0976f16acc9d33b93041f47b5bb548ba6a886fe818b6485dd0868aab`.
Audit records are under `/tmp/ce-resume-20261010/report-111-qa/`.

The contract has 151 declared components across 25 recursive files. All 151
appear in the atlas; 152/152 level child sets match. All 488 physical target
paths and responsibilities appear in the 25 inventories. Browser QA visited
all 456 scope/view states (152 each for Actual, Target, Diff), clicked 453
child cards, checked all 24 component detail inventories plus the root
inventory, and found all 17 finding IDs and 11 deviations. Report-to-detail,
back navigation, lens changes and reload retained the requested scope/view.
Final browser audit recorded zero failures. An initial zero-file read was a
render-timing race; after waiting for the inventory it showed all nine files.

At integrated Step 174 head `0e0b709c`, a fresh 1.1.1 report has 13 violations
and 254 canonical UNKNOWN records. It matches the reviewed Step 174 candidate
in every top-level section except `source.git_head`. The full browser matrix
was run on the earlier `019f9cbc` artifact; Step 174 changed contract selectors,
not report navigation code. These checks establish bounded report navigation,
not zero architecture violations, complete behavior parity or release acceptance.

LOCAL VERIFIED: static report/target reconciliation, browser navigation matrix,
and integrated report comparison.
CI-ONLY VERIFICATION: pending for the integrated head.
