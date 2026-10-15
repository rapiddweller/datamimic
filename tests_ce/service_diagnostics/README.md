# Mongo service CI diagnostics

The external service CI job runs its existing pytest command through
`mongo_diagnostics.py` while investigating
[issue #281](https://github.com/rapiddweller/datamimic/issues/281).
This collects evidence; it does not resolve the intermittent worker timeout.

The runner adds this directory and the repository to the child `PYTHONPATH`.
`sitecustomize.py` registers public PyMongo heartbeat and connection-pool listeners in the test
process and its spawned Python workers. Ordinary runs do not load this hook.
The test process also records pytest node IDs and phase outcomes, so timestamps
and parent PIDs connect a worker event to the preceding test sequence.

The always-uploaded `mongo-service-diagnostics-*` artifact contains:

- `environment.json`: Python/package versions, resolved lock hash when available,
  and the original test exit code.
- `events-<pid>*.jsonl`: UTC/monotonic timestamps, process/thread identity,
  heartbeat/connection-pool metadata, and test sequence markers.
- Independent authenticated pings every two seconds, using the same fixed test
  credentials as the service definition. Their two-second diagnostic timeout
  does not alter any runtime client option.
- Before/after Mongo container state/image ID and the last 20,000 service log
  entries. Docker is read through its local Unix socket. Only log timestamp,
  severity, component, numeric event ID and context survive the allowlist.

Commands, documents, replies, credentials, exception text, container environment,
and free-form server messages/attributes are excluded. Each PID retains a current
and previous event file, each bounded to 1 MiB; Docker responses are capped at
16 MiB. Docker or artifact I/O failures are best effort and do not prevent pytest
from starting or replace its exit code. Probe failures likewise do not change
test results. Forced cancellation can leave only the evidence already flushed;
the wrapper does not add signal forwarding or process-tree management.

Topology/server listeners are deliberately omitted: in pinned PyMongo 4.10.1,
their event executor can add approximately 500 ms to a short-lived client's close.
Heartbeat and pool callbacks avoid that executor. They retain worker identity,
addresses, heartbeat failure classes and fixed pool reason codes, while the
original pytest traceback still carries the final topology description. The
artifact does not include topology IDs or description-transition events.

Compare a timed-out worker's heartbeat/connection events with concurrent ping
results and the Mongo numeric log events. A green run or an isolated matrix pass
does not establish the historical cause or clear #281. Keep the native timeout,
descriptors, assertions, and full service test selection unchanged in CI.
