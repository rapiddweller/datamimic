# Amendment 81: IO interface ownership

Decision: Astra. For CE 5.0, supersede D4's compatibility clause only for these
`engine.io.api` exports: `FileUtil`, `database_count_query_length`,
`database_get_by_page_with_type`, `database_get_random_rows_by_columns`,
`is_mongodb_client`, `is_rdbms_client`, `mongodb_count_collection`,
`resolve_source_collection`. Remove their root bindings without shims.

This is a Python import break; external consumers are UNKNOWN. Migrate
`from datamimic_ce.engine.io.api import FileUtil` to
`from datamimic_ce.engine.io.files.api import FileUtil`. Domain generators
use existing dataset-loader operations. Internal client/source helpers keep
their existing owners. No 4.x patch/minor backport is authorized.

Keep reader/cache identity, open values, signatures, descriptor behavior and
retained Runtime/Authoring/script operations. Remove only the orphan root
properties allowance and root API's direct file requirement. The public file
interface remains declared; its boundary-type measurement gap remains open.
No baseline, budget, gate, descriptor or oracle change.

Supplemental decision: retire only the collection resolver's parent
IO-DATA-SOURCES public declaration. Its remaining caller is that component's
own router; the function, signature, owner and direct unit-test access stay.
This supersedes the instruction to retain that one local declaration. It
narrows a stale boundary promise, not a live implementation dependency.
