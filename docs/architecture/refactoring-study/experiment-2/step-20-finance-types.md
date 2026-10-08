# Step 20: Fixed finance result shapes

Amendment 61 corrects the initial CE ownership: the final TypedDicts live in
`datamimic_ce.domains.finance.contracts`, aligned with EE. `CurrencyData.name`
is optional because the account path returns only code and symbol;
`GeneratedTransactionData` replaces the local `TransactionData` name.

Independent Luna implementation and QA passes preceded root review. The
pre-fix checker report changed from 127 to 124 `boundary_types` violations;
`UNKNOWN` positions changed from 251 to 252. The additional UNKNOWN is
`get_currency`'s `return.name`: the EE-aligned `CurrencyData.name` is
`NotRequired[str]`, and ArchKeel currently treats `NotRequired` as generic at
this return boundary. CE constructs the `name` key on this path, but the
account-backed path omits it, so the shared type is correctly optional. This
is a checker limitation, not evidence of uncertain runtime behavior. The
three removed findings concern only these fixed return types. A separate
ArchKeel candidate checks `NotRequired[str]` and reports 124 violations and
251 UNKNOWN positions. `validate` still stops on 13 unrelated
`interface.unused` contract diagnostics; this step is not architecture-green.
The slice remains uncommitted until the checker fix is integrated.

LOCAL VERIFIED: `make lint`, `make typecheck` (488 files), the focused finance
and architecture tests (8 passed), and `make test-unit` (1418 passed, 11 skipped,
1 xfailed). The candidate report shows 488 observed and 488 target module paths
with no difference; all 148 target components and 488 target modules have a
responsibility sentence. A mypy positive/negative probe accepts an omitted
optional currency name and rejects mistyped required fields.
The two captured, unseeded finance descriptors
`tests_ce/integration_tests/test_entity/transaction.xml` and
`datamimic_ce/resources/demos/overview-generator/finance.xml` produce equal
structural records on frozen Step 0 and this tree under the same oracle.

CI-ONLY VERIFICATION: not run. Full descriptor recapture remains open.

## Separate pre-existing behavior finding

`Transaction.__init__` calls `get_transaction_type()` once and
`generate_transaction_data()` calls it again. With fixed RNG seeds 0–9, eight
transactions drew different type/direction pairs across the two calls. This
can combine a displayed transaction type with details from another draw. It
predates this step; fixing it would change seeded outputs and needs a separate
behavior decision and descriptor comparison.
