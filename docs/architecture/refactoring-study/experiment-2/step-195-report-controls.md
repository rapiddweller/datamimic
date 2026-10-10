# Step 195 — sampled report controls

Independent QA checks the immutable Step 192 report: 15 normal Tab traces,
41 Enter activations, 11 graph states for pan/zoom/fit, and eight light/dark
desktop/narrow viewport samples. Sampled navigation and controls work; Fit
overview contains every sampled card. No lost topology or extra UML model
is justified by this audit.

One label defect is reproduced: the UML `100%` button resets filters and
auto-fits, leaving module/class zoom at 140%/85%. Published 1.1.1 source
confirms the intentional reset-plus-fit action. After duplicate checking,
[ArchKeel #442](https://github.com/rapiddweller/archkeel/issues/442) requests
a consistent descriptive label. No CE or renderer change was made.

The [receipt](step-195-report-controls-receipt.json) binds inputs, raw browser
checks, screenshots and retained initial harness errors. Original report
provenance remains `72202ba0`, dirty with approved contract prose; no rescan
or claim of current-head generation follows.

LOCAL VERIFIED: bounded keyboard, pointer and visual checks; published-source
comparison and exact issue readback. CI-ONLY VERIFICATION: none for this audit.
Exhaustive traversal, fullscreen Escape, touch/HiDPI and universal UI acceptance
remain unproved. Fit overview at 11% does not establish readable method labels.
