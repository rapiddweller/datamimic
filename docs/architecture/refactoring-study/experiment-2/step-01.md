# Step 1 — remove the root service package

## Change

- moved source-template evaluation to `engine.runtime.evaluation`;
- updated its two production consumers;
- deleted the otherwise empty `services` package;
- removed the deleted legacy package from runtime ownership in the contract.

No wrapper or compatibility import remains. The path was internal.

## Verification

- authoritative serial source-script functional, integration, and nested-part tests: `10 passed`;
- changed-file Ruff: pass;
- `git diff --check`: pass;
- full-package mypy reached all 457 files and stopped on two pre-existing missing optional `ray`
  imports in untouched files;
- capabilities, authoring reference, and overview SHA-256: identical to Step 0.

## Architecture delta

- violations after the Amendment-02 measurement correction: 1,308 → 1,305;
- runtime placement violations: 68 → 66;
- root-layout violations: 24 → 23;
- all measurement budgets unchanged;
- observation completeness: pass.

ArchKeel reports six new and nine resolved fingerprints. Six are one-for-one path moves of the
same imports and `Any` positions from `services.source_script_evaluator` to
`engine.runtime.evaluation`; the other three resolved findings are the deleted package's two
placement facts and root child. `--accept-new` was used only for those six renamed fingerprints.
The generated amendment records the required removal of the no-longer-scanned legacy package from
component ownership.
