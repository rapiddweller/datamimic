# Datasource and reference coverage

This ledger names the committed descriptors that protect the runtime datasource
boundary. Matrix tests load these files from disk; they do not construct XML inline.

## Datasource matrix

| Consumer | Source | Paging | Descriptor |
|---|---|---:|---|
| `variable` | CSV | no | [`test_distribution_matrix/variable_csv.xml`](test_distribution_matrix/variable_csv.xml) |
| `variable` | CSV | yes | [`test_distribution_matrix/variable_csv_paged.xml`](test_distribution_matrix/variable_csv_paged.xml) |
| `variable` | JSON | no | [`test_distribution_matrix/variable_json.xml`](test_distribution_matrix/variable_json.xml) |
| `variable` | SQLite client | no | [`test_distribution_matrix/variable_sqlite.xml`](test_distribution_matrix/variable_sqlite.xml) |
| `variable` | memstore | no | [`test_distribution_matrix/variable_memstore.xml`](test_distribution_matrix/variable_memstore.xml) |
| `variable` | Python expression | no | [`test_distribution_matrix/variable_lazy.xml`](test_distribution_matrix/variable_lazy.xml) |
| `generate` | CSV | no | [`test_distribution_matrix/generate_source.xml`](test_distribution_matrix/generate_source.xml) |
| `generate` | CSV | yes | [`test_distribution_matrix/generate_source_paged.xml`](test_distribution_matrix/generate_source_paged.xml) |
| `nestedKey` | memstore | no | [`test_distribution_matrix/nestedkey_source.xml`](test_distribution_matrix/nestedkey_source.xml) |

Each valid descriptor exercises `ordered`, `random`, and `cumulated`; the Python
manifest in `test_distribution_matrix.py` asserts this ledger remains complete.

## Reference matrix

| Selection | Cyclic | Unique | Nested | Expected | Descriptor |
|---|---:|---:|---:|---|---|
| random | no | no | no | valid | [`test_reference_distribution/ref_random.xml`](test_reference_distribution/ref_random.xml) |
| ordered | no | no | no | valid | [`test_reference_distribution/ref_ordered.xml`](test_reference_distribution/ref_ordered.xml) |
| ordered | no | no | no | exhausted/error | [`test_reference_distribution/ref_ordered_exhausted.xml`](test_reference_distribution/ref_ordered_exhausted.xml) |
| ordered | yes | no | no | valid/wrap | [`test_reference_distribution/ref_cyclic.xml`](test_reference_distribution/ref_cyclic.xml) |
| ordered | yes | no | yes | valid/shared rotation | [`test_reference_distribution/ref_cyclic_nested.xml`](test_reference_distribution/ref_cyclic_nested.xml) |
| cumulated | no | no | no | valid | [`test_reference_distribution/ref_cumulated.xml`](test_reference_distribution/ref_cumulated.xml) |
| random | no | yes | no | valid/distinct | [`test_reference_distribution/ref_unique.xml`](test_reference_distribution/ref_unique.xml) |
| random | yes | yes | no | parse error | [`test_reference_distribution/ref_unique_cyclic_invalid.xml`](test_reference_distribution/ref_unique_cyclic_invalid.xml) |

The Python manifest in `test_reference_distribution.py` asserts all descriptors
exist and that the expected selection/cyclic/unique/nested cells remain covered.

## Authoring reference surface

Runtime coverage is complemented by:

- `unit_tests/test_authoring/test_reference_topic_transport.py`: every typed
  `ReferenceTopic` and every `AuthoringReferenceCategory` has CLI/service parity.
- `unit_tests/test_authoring/test_source_capability_matrix.py`: the capability
  catalog projects consistently to lint, manifest, reference text, and the
  `DataSourceRegistry` architecture boundary.
