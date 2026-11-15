# Scenario projects that need PostgreSQL or MongoDB

Three projects of the scenario corpus (issue #411) that need a service. The corpus in `tests_ce/scenarios` holds only
file, SQLite and targetless projects, so these live here, with the other external-service tests.

| Project | What it shows |
|---|---|
| `s50_postgres_readback` | S7 on PostgreSQL: clear a table, write 12 rows, read them back, check the values in the run. |
| `s51_mongo_readback` | S7 on MongoDB: clear a collection, write 12 documents, read them back, check the values in the run. |
| `s52_mongo_to_postgres` | X6: clean both targets, write 12 raw documents to Mongo, transform them into a Postgres table, read the table back and check each row against its source. |

`test_scenario_services.py` has the contract of `tests_ce/scenarios/test_scenarios.py`: Build is `ready`, a run gives the
rows in `scenario.json`, a second run gives the same rows, and each negative is rejected with its diagnostic. It adds a
state check that reads the services directly.

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
