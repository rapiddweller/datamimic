# Step 08C20: isolate XLSX integration cases

## Change

- Both XLSX test modules now copy their unchanged XML descriptors into a
  function-scoped `tmp_path`. Inputs and generated XLSX files stay there.
- Removed cleanup against the shared source directory. All prior assertions
  remain; production code and descriptor bytes are untouched.

## Evidence

- Independent implementation and review passes found no lost assertions or
  changed XML. The review ran all 15 tests with four xdist workers.
- Orchestrator reran all 15 tests serially and with two xdist workers; both
  passed. The test directory contains no generated XLSX or `output/` artifacts.
- The implementation agent's deliberate failure probe confined its workbook
  and output to the case's temporary directory. Pytest manages failed temp
  directories for debugging; no shared test path is written.
- Ruff and `git diff --check` pass. The sandbox blocks the unrelated
  `pytest-rerunfailures` localhost bind, so these runs used
  `-p no:rerunfailures`.
