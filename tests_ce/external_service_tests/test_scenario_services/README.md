# Scenario projects that need PostgreSQL or MongoDB

Five projects that need a service: three of the scenario corpus (issue #411) and two for createTable. The corpus in `tests_ce/scenarios` holds only
file, SQLite and targetless projects, so these live here, with the other external-service tests.

| Project | What it shows |
|---|---|
| `s50_postgres_readback` | S7 on PostgreSQL: clear a table, write 12 rows, read them back, check the values in the run. |
| `s51_mongo_readback` | S7 on MongoDB: clear a collection, write 12 documents, read them back, check the values in the run. |
| `s52_mongo_to_postgres` | X6: clean both targets, write 12 raw documents to Mongo, transform them into a Postgres table, read the table back and check each row against its source. |
| `s53_postgres_create_table_schemas` | `createTable` on two PostgreSQL clients with one schema each: the table is created in each schema, and a table of the same name in `public` stays untouched. |
| `s54_mongo_collection_without_table` | MongoDB needs no table: the first write creates the collection, and `createTable` on a MongoDB target is refused with I984. |

`test_scenario_services.py` has the contract of `tests_ce/scenarios/test_scenarios.py`: each Build outcome and its exact
coverage facts (uncovered products, unread files, unchecked sinks, and seed state) are declared in `scenario.json`;
a run gives the listed rows, a second run gives the same rows, and each negative is rejected with its diagnostic. The
runner excludes only the root `scenario.json` from the Build workspace because it is test metadata, not model input.
It adds state checks that read the services directly, and a `run_error` for negatives where a failed `<assert>` must
also stop a normal run (`run_assert_*`).

The current coverage gaps are intentional: fixture seed files are loaded into the services by the test rather than
read by the model; generated totals/check products and declared database sinks do not have separate Build
expectations. Those gaps do not weaken the run assertions or the service-state checks.

## Run

CI runs this folder in the `external_service_test` job (services `postgres` and `mongo`, `conf/environment.env.properties`).
Locally, start the services on the ports of `conf/local.env.properties` (PostgreSQL 45432, MongoDB 47017) and run:

```bash
RUNTIME_ENVIRONMENT=development pytest tests_ce/external_service_tests/test_scenario_services -q
```

## What Build proves here

The same limits as `s39_sqlite_readback` hold:

- Build refuses an `<execute>` step, so a project cannot create its own table. The test loads `db/seed.sql` and
  `db/seed.json` first. They hold the rows that the seed writes.
- Build isolates the write targets and skips the clears (`not_executed`). The readback in Build shows the seeded rows,
  not the rows of the load. The `<assert>` elements of the readback step and the state checks of the test prove the
  delivery in a normal run.
- The literal `count` on a readback works around #493 and is marked in the XML.
- A MongoDB readback keeps the `_id` of each document, a new value on every run. The replay check leaves it out.
