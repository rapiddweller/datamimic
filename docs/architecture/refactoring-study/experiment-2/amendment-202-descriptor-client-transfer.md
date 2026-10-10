# Amendment 202 — descriptor client transfer

Decision: implement Amendment 199 within the existing Context, SetupTask,
GenerateWorker and IO clients boundaries; retain Amendment 155.

IO owns same-process include cloning: preserve native wrapper/cache state,
exclude the live RDBMS engine, and leave parent resources and injections alone.
`clone_client_for_include` is published through the existing IO API and the
already-public operations module. No dependency permission or selector changes.

Context carries typed recipes, non-owning object/config history and worker
payload state. SetupTask owns ordered binding before task construction and
scope cleanup. GenerateWorker owns three separate transport graphs and local
receiver reconstruction/cleanup. These use existing published modules/classes.
Retired captures retain their original config; current client-map aliases and
namespace rebindings remain distinct. Worker capture starts empty; required
Memstore and prepared generator state remain native.

These are implementation decisions, not acceptance evidence. Actual process
ownership, DSL parity and failures require the Step 202 tests and service proof.
Arbitrary custom captures/reducers and Ray process isolation remain UNKNOWN.
