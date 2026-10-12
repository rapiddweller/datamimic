# Step 08C33: audit 11 local policy-only descriptors

The service-suite inventory contains 116 XMLs without an explicit service
client. A separate Luna safety pass approved only 11 local-source/memstore
cases. The runner pins each XML and fixture hash, checks both checkout
revisions and clean production packages, rejects service/script/include/file
targets and unsafe paths, and stages only audited inputs. Execution is opt-in.

The first run stopped before executing a descriptor: resolving the chosen
`.venv/bin/python` symlink launched base Python without venv dependencies.
The runner now preserves the invocation path and reports its real path
separately. Independent QA reproduced the negative control and passed the
first descriptor on both revisions before the full run.

The full frozen/target run at `a219163e` / `f312a455` then passed **11/11**
path comparisons. Every case was captured successfully on both sides with
matching product names, row counts, compatible value shapes, and output paths.
Independent QA checked every path, revision, interpreter, XML and fixture hash,
and recomputed equivalence. Evidence class is `normalized_unseeded`, not exact
row-value parity. Report SHA-256:
`14e5dd414e490627d3ffcbda0226ee30f45d0f6a5c1e0112a918e849d8f58e8b`.

| Descriptor group | Individually matched paths |
|---|---:|
| `data_source_cyclic`: CSV, JSON, memstore and part variants | 8 |
| `integration_data_source_cyclic`: CSV, JSON and product | 3 |

The exact paths and their pinned hashes are in
`script/architecture_study/compare_policy_only.py`. The per-path ledger points
to this step; the remaining policy-only cases are still `UNVERIFIED`.
