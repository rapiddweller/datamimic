# Step 08C22: compare remaining isolated SQLite cases

## Control

- Frozen Step 0: `a219163e`; target: `658f3a5f`. No production or XML
  changes between the target and this evidence step.
- Each run used copied, byte-identical XML and inputs, separate SQLite files,
  and asserted the imported checkout. Four demo owners executed eight included
  fragments in order. No shared service or container was used.
- Verifier SHA-256:
  `4e34e98c35f8a20a53854b2944bfa24cfdfc1ced8d0fa41ef90e2f44424e1f1f`;
  comparator SHA-256:
  `e1fa07b4ca426ecfa138a1a8d06fa5754cddd57b78c65759ed0d1c1fc7eac5e6`.
  The service-staging orchestration was inline, not saved; this limits exact
  replay of this batch.

## Results

Fifty-five newly paired XMLs: 19 seeded/exact captured-row comparisons; 36
unseeded or error cases with normalized outcome, count, shape, or diagnostic
parity. These categories are not interchangeable. Eight cases produced the
same expected error on both revisions; none was counted as successful DSL
execution.

| Batch | XMLs | Combined evidence SHA-256 |
|---|---:|---|
| Reference/composite/binary first slice | 5 | Per-case digests retained; no combined digest |
| Reference/composite second slice | 5 | `aee1bff990352c4b45970889d5aea4599ac106d11ac539758c801157eb17ef92` |
| Seeded reference/composite | 5 | `382e17800de7e5222c7e18e015179461a899e12cedb443c5b9b75d9a1567b676` |
| Invalid/conditional/delete sequence | 4 | `06681ef1cedd488b4c252ea0e1a6db3da07fda0544c593ee3671005e23aeb3e4` |
| Unseeded inline SQL | 5 | `d5a9467a02d4d49300363ac243902f61770b87fb2e2a5c231d4671c970f8dd98` |
| Unseeded SQL/scripts | 5 | `356d14bdb24d2fee57b0d96602d6a5baeadf77e7ef3a4e5502cba1b51521ac9f` |
| Remaining inline SQLite | 13 | `2f866826bcfdc74d7dcb579f3a8e084deeb95cc6795e61fbecefe8b3e59f6e88` |
| Config-selected SQLite | 5 | `115d813b1e111616e148b7e2d590bd15ea5449a6687dbc9085da48e6586776fc` |
| Four demo owners, eight fragments | 8 | `524e5ee7220ff810c6d4cd7e2cf64e056fd2e1cc087dc7104b3daaf400935770` |

Inventory by batch (directory is relative to its owning test/demo tree):

- First slice: `test_reference_distribution/{ref_cyclic,ref_unique,ref_ordered_exhausted}.xml`,
  `test_composite_reference/composite_three_fields.xml`,
  `test_binary_type/uc_document_vault.xml`.
- Second slice: `ref_cyclic_nested.xml`, `ref_random.xml`, `composite_mp.xml`,
  `composite_paged.xml`, `fk_integrity.xml` in their reference/composite test directories.
- Seeded reference/composite: `composite_exhausted.xml`,
  `composite_nonunique.xml`, `fk_unique_assignment.xml`, `legacy_single.xml`,
  `ref_cumulated.xml`.
- Invalid/conditional/delete: `ref_unique_cyclic_invalid.xml`,
  `insert_order_condition.xml`, `delete_order_phase1.xml`, `delete_order_phase2.xml`.
- Inline SQL: `test_execute_inline/inline_sql.xml`,
  `test_source_read_determinism/sqlite_unseeded.xml`,
  `test_sql_crud_targets/{sql_delete,sql_upsert}.xml`,
  `test_entity_stringify/test_entity_stringify_rdbms.xml`.
- SQL/scripts: `sql_update.xml`, `sql_update_no_pk.xml`, `execute_script_sql.xml`,
  `execute_script_and_body.xml`, `execute_script_and_uri.xml`.
- Remaining inline: `source_target_entity/{target_entity,backward_compat,source_entity}.xml`,
  `test_dbunit/read_to_db.xml`, `test_iterate_offset/test_offset_client_rejected.xml`,
  `test_rdbms_unknown_kwargs/unknown_kwarg.xml`,
  `test_execute_script/execute_script_non_string.xml`,
  `test_memstore_api/test_memstore_remove_not_existing_ids.xml`,
  `test_entity_matrix/{te_rdbms_delete,se_variable,te_rdbms,te_rdbms_update,se_rdbms}.xml`.
- Config-selected: external `test_rdbms/test_sqlite.xml`, external
  `test_rdbms_sql_matrix/matrix_sqlite.xml`, functional
  `test_sqlite/{datamimic,more_sqlite_test}.xml`, integration
  `test_if/test_complex_if.xml`.
- Demo fragments: `b-simple-database/{1_prepare,2_generate}.xml`,
  `demo-db-mapping/{1_prepare,2_mapping}.xml`,
  `e-simple-compositekey/{1_prepare,2_generate}.xml`,
  `k-watermark/{1_prepare,2_watermark}.xml`.

The matching-error cases were `ref_ordered_exhausted`,
`composite_exhausted`, `ref_unique_cyclic_invalid`, `sql_update_no_pk`,
`execute_script_and_body`, `execute_script_and_uri`,
`test_offset_client_rejected`, and `execute_script_non_string`. Demo mapping's
input script differs only by relocated imports; after normalizing those imports,
its bytes match Step 0. The demo evidence is in
`/tmp/dm-sqlite-demo-aggregates-proof-ulfxpec5`.

The service-classified ledger moves from 44 paired / 229 outstanding to 99
paired / 174 outstanding. One 200,000-row SQLite page-process case is still
unrun. No claim of full descriptor parity or delivery readiness follows.
