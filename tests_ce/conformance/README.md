# CE / EE conformance cases

These cases are the contract between the CE and EE sessions for #387. CE publishes the files.
Each edition runs the same files with its own runner and reports pass or fail per case.

## Layout

```text
cases/<id>/descriptor.xml   the entry descriptor
cases/<id>/expected.json    the expected outcome
```

The case id starts with `ok_` or `error_`. A case holds the descriptor only. It never holds values.

## `expected.json`

| Field | Meaning |
|---|---|
| `area` | `runtime`, `error-handling`, `logging` or `authoring` |
| `outcome` | `ok` or `error` |
| `products` | For `ok`: product name to row count. Names that are not listed are not checked. |
| `issue_code` | For `error`: the catalog issue code, for example `I928` |
| `error_code` | For `error`, optional: the error code, for example `E014` |
| `edition_notes` | Optional. A difference on purpose, per edition, with the reason. |

A case never compares messages, paths or row values. The codes and the counts are the contract.

## Runner contract

1. Copy the case directory to a new temporary directory.
2. Make that directory the working directory. SQLite files live under it.
3. Run `descriptor.xml` in the process, with the test API of the edition. Do not use the `run` CLI of EE,
   because it needs Platform settings (task id, Redis and MinIO).
4. For `ok`, count the rows of each product in `products`.
5. For `error`, expect one catalog error. Compare `issue_code`, and `error_code` when present.
6. A case with an `edition_notes` entry for your edition may fail. Report it as `known-difference`, not as `fail`.

The CE runner is `test_conformance.py`:

```bash
. .venv/bin/activate && pytest tests_ce/conformance
```

## Add a case

1. Write the smallest descriptor that shows one behavior.
2. Run it in CE and read the real outcome. Do not guess the code.
3. Write `expected.json`. Add `edition_notes` only for a difference on purpose.
4. Add the case to the matrix row in `docs/architecture/inner/ce-ee-parity.md`.
