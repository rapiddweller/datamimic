# Amendment 37: move live reference rendering to adapters

Move reference and capability rendering to `authoring/adapters/reference.py`.
It reads Runtime generator capabilities; `reference_projection.py` remains the
runtime-free typed intent projection. No shim or injected capability layer.

Evidence: recursive physical-target checks pass; the candidate ArchKeel report
drops from 24 to 23 violations with 71 UNKNOWN unchanged and no new violation.
The non-service suite passes (1962 tests, 13 skips). The 930-descriptor oracle
keeps every status and seeded result; one unseeded dynamic Memstore row count
varied, as it also does on same-code repeats. The frozen capabilities hash
still differs from step 0.
