# Blind-agent authoring eval

This eval measures how well an agent builds a project with the installed `datamimic` CLI alone.
The agent is a separate `claude -p` process with no project instructions, no memory and no skills. It gets one brief and an empty directory.
The brief asks for a project that `datamimic authoring build` reports `ready` for. Build needs the agent's own `acceptance/build.json`.
That file does not decide the verdict: an independent oracle judges the rows that the finished project produces.

Issue: #412. Scope of this directory: the cases, the oracle, the transcript audit and this protocol.

## Layout

```
benchmarks/authoring_eval/
  README.md            this protocol
  oracle.py            python -m benchmarks.authoring_eval.oracle <case> <project-dir>
  audit_transcript.py  python -m benchmarks.authoring_eval.audit_transcript <transcript.jsonl> ...
  run_subject.py       python -m benchmarks.authoring_eval.run_subject <case> --venv <venv> --model <model>
  brief.md             the brief of every subject; run_subject.py fills it in
  cases/<id>/
    prompt.md          the only text the subject sees
    oracle.json        the checks (hidden from the subject)
    fixtures/          files given to the subject with the prompt (only some cases)
    fixtures_changed/  the same files with other values; the oracle runs the project with them too (hidden)
    reference/         a good project; the positive test of the oracle (hidden)
    README.md          the prompt-to-check mapping and the equivalence classes (only e06, e07; hidden)
  results/             short Markdown summaries of finished campaigns
```

Raw transcripts and run directories stay outside the repository.

## Cases

| Id | Class | Domain | What it tests |
|---|---|---|---|
| e01 | simple | flat dataset | count, unique id, closed value set, numeric range, generated text that differs per ticket |
| e05 | simple | prices | closed value set, two ranges, one rule across two fields; one constant value per field passes too |
| e02 | complex | parent and child | exact count per parent, a parent key in each child, unique id over all children; a flat project passes too |
| e03 | complex | parent and child | the exact 12 slot rows of a prescribed `slot_id` formula, with no helper field; a literal table of the rows passes too |
| e04 | complex | CSV to JSON | comma separator, text to number, derived field, field subset, file output, rows that come from the input |
| e06 | complex | staffing register | five tables, foreign keys, counts per parent, a unique pair, a closed set, a derived field, an assignment that needs an employment of the same person, company and function and a license valid on its date (both days count, no expiry is never valid) |
| e07 | complex | two CSV files to JSON | a join with a default, a threshold filter, a tier discount rounded down, a date window with both days included, an exact field subset, rows that come from the input |

## Oracle checks

`oracle.json` holds a list of typed checks. Pydantic validates it. A check passes when:

| Kind | Passes when |
|---|---|
| `build_ready` | `datamimic authoring build` on the project reaches `ready`. Build needs the agent's own `acceptance/build.json`. |
| `exact_count` | the product has exactly `n` rows. |
| `unique` | every value of the field is a text or a number, and no value repeats. Floats and texts are accepted. |
| `whole_number` | every value is a Python `int`. A `bool`, a float and a text fail. |
| `per_parent_count` | each parent key owns exactly `n` child rows. Keys are compared as text, so keep `whole_number` on the parent key. |
| `value_in` | every value is in `values`. |
| `range` | every value is a whole number (as `whole_number`) from `min` to `max`, inclusive. |
| `text` | every row has the field, and the value is a text that is not empty. A number, `None` and `""` fail. A numeric string such as `"123"` and a blank string pass, so `script="str(ticket_id)"` passes. |
| `unique_together` | every row has each of `fields` as a text or a number, and no two rows hold the same combination. One field alone may repeat. |
| `row_exists_in` | for each row of `product`, a row of `target` holds the same `fields` with the same JSON types (`1` is not `"1"`). With a `window`, the `date` field of the row is also from the target's `start` to its `end` field, both days included. A bound that is null, empty, absent or not a `YYYY-MM-DD` date never matches, so a missing expiry date is never valid. |
| `date_range` | every value is a `YYYY-MM-DD` text of a real day from `min` to `max`, inclusive, except exactly `missing` nulls. An empty text is not a null; a row without the field fails. |
| `field_at_most` | in every row, both fields are numbers and `field` is at most `other`. |
| `exact_rows` | the captured rows equal `rows`. Row order is ignored. Keys and JSON types must match. With `ignore_extra_fields: true`, only the fields that `rows` names are compared (e03 depots: the prompt fixes the field set for slots only). |
| `output_rows` | the run with the case directory `fixtures` laid over `fixtures/` produced the product and wrote `<product>.json`, or the chunk parts `<product>_<n>.json`, and their rows equal `rows` (as `exact_rows`). |
| `fixtures_unchanged` | every file of the case directory `fixtures` is in the submitted `fixtures/`, byte for byte. A changed or deleted file fails; a new file passes. The prompt says not to change the file. |
| `seed_is` | `<setup rngSeed>` of the entry `datamimic.xml` is `seed`. The agent's `acceptance/build.json` is never read. |
| `repeatable` | two runs give the same rows in the same order. The runs use separate copies and interpreters, with `PYTHONHASHSEED` `1` and `2`. Build also replays a seeded project under another hash seed, so a hash-order project fails `build_ready` too. |

The oracle compares the submitted `fixtures/` with the case fixtures first. Then it copies the project to private directories and lays the case fixtures over each copy.
It runs `Build` on one copy. It runs the other copies at the same time and captures the rows per product from each run.
Every row check reads the rows of the first run. An `output_rows` check with another `fixtures` directory gets one more run with that directory.
The verdict is JSON. It holds one short reason for each check and no row value.
The exit code is `0` when all checks pass and `1` otherwise.

Limits of the oracle:

- `per_parent_count` groups the child rows by the parent key. It does not prove that a child sits under the right parent when two parents swap keys.
- The oracle checks values, not the method. The fix review wrote these projects, and they pass:
  - e03: a global counter gives wrong values and fails. A flat project that computes the per-depot counter by arithmetic passes. A literal list of the 12 `slot_id` values passes, because the prompt fixes all 12 rows. e03 proves the arithmetic, not nested authoring.
  - e02: a flat `invoices` product with `subscriber_id = (invoice_id - 1) // 3 + 1` passes.
  - e05: `tier=GOLD`, `list_price=900`, `sale_price=50` in all 40 rows passes. That is literal compliance with the prompt.
- e06: the subject makes its own data, so a rule binds only the rows the subject makes. A project that never puts a work date on an expiry day passes, though it can count the expiry day as invalid.
  The prompt requires 10 licenses without an expiry date, so "no expiry is never valid" binds every submission. The reference and the variants prove each boundary of the check.
- e06: a project that types all 124 consistent rows passes. The oracle proves the values, not the generation, as for e03.
- The capture writes a value that is not JSON as its text. A Python `date` becomes `"2026-03-01"` and passes `date_range`; a `datetime` becomes `"2026-03-01 00:00:00"` and fails it. The prompt asks for a text, and the oracle cannot see that difference.
- `row_exists_in` proves that a matching row exists, not that the project intended that row: a project can match by chance. With the case seed, the cheat with random foreign keys fails: its 20 random assignments do not all match an employment.
- e04 proves that the rows come from the CSV with a second CSV of other values (`fixtures_changed/`). It does not prove how the project reads the file.
  A project that reads its own copy of the CSV at another path fails that check. The prompt names `fixtures/orders.csv`, so this is intended.
- e07 proves the same with `fixtures_changed/`, which also has another number of orders and of kept orders. The oracle reads only the `order_report` files, so a helper product may write another file.
- The engine names a product nested two levels deep `inner|leaf`. The capture names it `leaf`, as Build does. Build refuses two products with the same name.
- The answer key is on disk: in this repository, in other checkouts of it, and in the transcripts of the sessions that wrote the cases (`~/.claude/projects`).
  The sandbox blocks Bash reads of this checkout and of `~/.claude/projects` only. So e04 proves that the rows come from the CSV only for a subject that does not search the disk. Read the transcript.
- `repeatable` finds a difference that two hash seeds expose. The engine fixes the clock and the random generators when the seed is set, so a script cannot use them to make a seeded run differ.

## Protocol

Follow these steps for every run. One run is one `claude -p` process for one case.

1. Freeze the commit. Write the commit SHA in the results file.
2. Build the wheel: `uv build --wheel`.
3. Make a fresh virtual environment for the run, outside the repository and in a directory whose path does not name the product.
   The Bash sandbox blocks reads of the repository, so a venv inside it does not run:
   `uv venv <venv>` then `uv pip install --python <venv>/bin/python <wheel>`. Do not reuse a venv between runs.
4. Start the subject: `python -m benchmarks.authoring_eval.run_subject <id> --venv <venv> --model <model>`. Record the JSON report.
5. Run the oracle from the frozen checkout with its own venv, not the venv of the subject: `python -m benchmarks.authoring_eval.oracle <id> <run-dir>`. Record the verdict.
   WARNING: the oracle executes untrusted project code without a sandbox. Build runs it in the oracle process, with the full environment.
   Each capture run is a child process with the project copy as the cwd and only the variables of the runner (see below).
6. Delete the run directory, its parent and the venv after the record is complete.

### What the runner does

1. It makes a fresh temporary directory `<base>` and the run directory `<base>/run`. It copies `cases/<id>/fixtures/` into the run directory when the case has fixtures.
2. It writes `<base>/AGENTS.md` and `<base>/CLAUDE.md`. Both hold a unique canary token. The brief does not mention them.
3. It fills in `brief.md` and starts `claude -p` with the run directory as the cwd and these flags:

   | Flag | Effect |
   |---|---|
   | `--safe-mode` | no CLAUDE.md, AGENTS.md, memory, skills, installed plugins, hooks or MCP servers |
   | `--restricted` | the user, project and local settings files are ignored; the file tools stay in the cwd (a probe `Read ../PARENT.md` was denied) |
   | `--settings` with `sandbox_settings()` | the Bash sandbox of Claude Code: see [Bash sandbox](#bash-sandbox) |
   | `--tools` and `--allowed-tools` `Bash,Read,Write,Edit,Glob,Grep` | only these tools exist, and they need no prompt |
   | `--permission-prompts none` | any other permission request is denied |
   | `--disable-slash-commands`, `--strict-mcp-config` | no skills or commands, no MCP servers |
   | `--no-session-persistence` | the run cannot be resumed; long tool output still goes to `~/.claude/projects/<run>/…/tool-results/` |
   | `--max-budget-usd 3` | a cost limit; the CLI has no turn limit flag |
   | `--output-format stream-json --verbose --debug-file` | the transcript and the debug log, both in `<base>` |

   The child gets only `HOME`, `USER`, `LOGNAME`, `LANG`, `TMPDIR`, `SHELL` and a system `PATH` (`oracle.child_env`).
   The child runs in its own process group. On a timeout (30 min), and after every run, the runner kills that group. A stand-in CLI proves that its child dies too.
4. It checks the isolation (`isolation_problems`) and audits the transcript with `--allow <run-dir> --allow <venv>/bin/datamimic --forbid <repository-root> --canary <token>`.
   It also allows the `tool-results` directory of the run's own session (`own_tool_results`), when the init message names a session id that is a UUID.
5. It always prints a JSON report with the run directory, the CLI version and the result line. The exit code is `0` only when the report has no problem and no finding.

The isolation check fails the run when:

- the CLI did not finish before the timeout, or its exit code is not `0`;
- the init message is missing, its `tools` are not the allowlist, or it lists skills, MCP servers or slash commands;
- the cwd of the subject is not the run directory;
- the result message is missing, reports an error, or reports a denied tool call (an access or configuration error, not a model failure);
- the debug log is missing or not UTF-8, or does not show `project memory is off` (safe mode) and `Sandbox: ignoring permission rules` (the sandbox settings loaded);
- the debug log names a canary file (in the `/var` or the `/private/var` spelling), or shows that a hook added context;
- a file in the run directory holds the canary, or cannot be read.

The audit adds a finding for a transcript line that is not one JSON object, because such a line can hide a tool call.

Evidence from Claude Code 2.1.304, with a model name that does not exist (no API call): without `--safe-mode`, the debug log shows
`AGENTS.md loaded: <base>/AGENTS.md` and a SessionStart hook with `additionalContext`, and the isolation check reports both.
With `--safe-mode`, the debug log shows `project memory is off`, and the init message lists no skills.
When the CLI version changes, repeat that probe without `--safe-mode` and confirm that the isolation check still reports the leak.

### Bash sandbox

`--allowed-tools Bash` approves every Bash command. Without more, a subject can delete or send anything that the user can.
The runner therefore passes `--settings` with the Claude Code Bash sandbox ([docs](https://code.claude.com/docs/en/sandboxing)):

```json
{"sandbox": {"enabled": true, "failIfUnavailable": true, "allowUnsandboxedCommands": false,
             "filesystem": {"denyRead": ["<repository-root>", "~/.claude/projects"]}}}
```

- `enabled`: every Bash command runs in the macOS Seatbelt or Linux bubblewrap sandbox. Writes stay in the cwd and the sandbox temp directory. The network goes through a proxy that refuses each host that is not allowed, because nobody answers the prompt.
- `failIfUnavailable`: the CLI does not start when the sandbox cannot start.
- `allowUnsandboxedCommands: false`: the CLI ignores `dangerouslyDisableSandbox`. Without it, the `Bash` allow rule approves an unsandboxed retry.
- `denyRead`: the repository and the transcripts of earlier sessions hold the answer key.

Evidence from Claude Code 2.1.304 on macOS, with three Haiku probes (USD 0.0076 in total). Each probe made one Bash call with the flags of the runner:

| Command in the probe | without `--settings` | with `--settings` |
|---|---|---|
| `rm` of a canary in a fresh `$TMPDIR` directory, outside the cwd | deleted | `Operation not permitted` |
| `rm` of a canary in a fresh `/tmp` directory | deleted | `Operation not permitted` |
| `rm` of a canary in a fresh `/tmp/claude-<uid>` directory (the sandbox temp directory) | not probed | **deleted** |
| `curl https://example.com` | `200` | `CONNECT tunnel failed, response 403` |
| `wc -c <repository>/…/e04/oracle.json`; `ls ~/.claude/projects` | read | `Operation not permitted` |
| `touch` in the cwd; `<venv>/bin/datamimic authoring build .` (venv outside the repository) | ok, `ready` | ok, `ready` |

The debug log shows no line for each sandboxed command. It shows `Sandbox: ignoring permission rules …` only when the sandbox settings load, so the isolation check requires that line.
Keep that check. In `-p` mode the CLI silently ignores a settings value that fails validation, so one unknown key can turn the sandbox off without an error; `failIfUnavailable` does not catch that.
Do not add a sandbox key without a new probe.
Repeat the probes (`rm` outside the cwd, `curl`) when the CLI version changes.

What stays unproven:

- The canary sits only in the parent directory. Safe mode states that it turns off the user `~/.claude/CLAUDE.md` too, but no canary proves it. The runner does not edit the user's files.
- A clean config home is not possible with a keychain login: an empty `CLAUDE_CONFIG_DIR` gives `Not logged in`. `--bare` needs `ANTHROPIC_API_KEY`. The subject therefore uses the real login and the real `~/.claude`.
- The init message still lists the installed plugins. The debug log says safe mode does not load them.
- The sandbox temp directory is `/tmp/claude-<uid>`, and Bash can write and delete there. It holds the temporary files and the scratchpad of every Claude Code session of the same user, including the session that starts the runner. `CLAUDE_CODE_TMPDIR` did not move it. Before a campaign, keep nothing there that you need.
- The process-group kill is proven with a stand-in CLI only. No probe showed that Claude Code keeps the Bash commands of the subject in its process group.
- Bash can read every file that the user can read, except the two `denyRead` paths. Other checkouts of this repository hold the answer key too.
- The oracle has no sandbox (see the protocol, step 5).
- The turn limit is a rule of the brief. The report counts the tool calls.
- No run has shown a model that writes the canary token. The leak that was caught came from the debug-log check.
- A run that reaches `--max-budget-usd` probably ends with `is_error` and is then void, though it is a model failure. The exact result fields of a budget stop are not verified; read the `result` of the report.

### Subject brief

`brief.md` holds the brief. The runner replaces the words in angle brackets. Put no other text in the brief. Do not add hints.
The turn limit is 40 tool calls for every case. A rule that the audit cannot check (rule 1, rule 7) is checked by reading the transcript.

### What to record for each run

| Field | Source |
|---|---|
| model | the runner command |
| tool calls | the runner report |
| tokens, cost, duration | the `result` line of the transcript |
| first Build call and its outcome | the transcript |
| final Build outcome | the `build_ready` check of the oracle |
| oracle verdict | the oracle output |
| isolation and audit verdict | the runner report |

A run is first-try `ready` when the first `datamimic authoring build` call of the agent returns `ready` and the oracle passes on the final project.
A run is a pass within the turn budget when the oracle passes on the final project and the agent used at most the turn limit.

### Void runs

A run is void when the runner reports a problem or the audit finds a forbidden action. The forbidden actions are:

- any tool outside `Bash`, `Read`, `Write`, `Edit`, `Glob` and `Grep`;
- any tool call that touches a path under the repository root;
- any mention of `AGENTS.md` in a tool call;
- any read or write of a file outside the run directory, except a run of `<venv>/bin/datamimic` (so the installed source stays unread)
  and the `tool-results` directory of the run's own session, where the CLI saves a long tool result and tells the model to read it.
  A path that does not exist, such as a typo, still counts: it is an access attempt;
- the canary token anywhere in the transcript.

A void run does not count in any rate. Repeat it with a new process. List the void runs in the results file with the finding.

The audit reads the tool calls of the assistant for tools and paths, and every line for the canary. It reads shell commands for absolute and `~/` paths only.
It checks an absolute or `~` `Glob` pattern from its root: the directory before the first glob character. A `..` after a glob character makes the root `/`.
A void run can pass the audit. The fix review found that the audit misses these Bash forms:

| Form | Example |
|---|---|
| a variable | `cat $HOME/.claude/CLAUDE.md`; `D=<venv>/bin/datamimic; cat ${D%/bin/datamimic}/lib/…` |
| a bare `~` | `find ~ -name orders.csv`; `cd ~ && cat .claude/CLAUDE.md` |
| a bare `/` or `//` | `find / -name oracle.json`; `ls //`; `cd // && cat etc/passwd` |
| a relative path | `ls $PWD/../..`; `rm -rf ../../*`; `cat ../AGENTS.md` is flagged only by its name |
| a glob | `cat ../AGENT?.md`; `cat ../C*.md` |
| a changed canary | `cat ../CLAUDE.md \| tr a-z A-Z` |
| an interpreter under `/usr` | `/usr/bin/python3 -c "open(…/.ssh/config)"`; `/usr` is allowed |
| the network | `curl -s https://…` |

The audit also misses a relative file-tool path such as `Read file_path=../CLAUDE.md`. `--restricted` denies that read, and the denial voids the run.
The sandbox blocks the network and the writes outside the cwd and the sandbox temp directory for every form above, but not all reads (see [Bash sandbox](#bash-sandbox)). Read the transcript when a result looks too good.

## Targets

| Class | Cases | Target |
|---|---|---|
| simple | e01, e05 | at least 95 % of runs are first-try `ready` and pass the oracle |
| complex | e02, e03, e04, e06, e07 | at least 80 % of runs pass the oracle within the turn budget |

Run every case with Haiku, Sonnet and Opus. Do at least five runs for each model and case.
Void runs do not count towards the five.

## Results

Write one short Markdown file for each campaign to `results/<date>-<commit>.md`:

1. the commit SHA and the wheel version;
2. one table: case, model, runs, first-try `ready`, oracle pass, void;
3. the failure classes, each with an issue number or a documented limit;
4. the void runs and their findings.

Do not commit raw transcripts, run directories or agent output.
