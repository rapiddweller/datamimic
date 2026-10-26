# Blind-agent authoring eval

This eval measures how well an agent builds a project with the installed `datamimic` CLI alone.
The agent is a sub-agent with no context and no skills. It gets one prompt and an empty directory.
An independent oracle judges the rows that the finished project produces. The agent's own `acceptance/build.json` does not count.

Issue: #412. Scope of this directory: the cases, the oracle, the transcript audit and this protocol.

## Layout

```
benchmarks/authoring_eval/
  README.md            this protocol
  oracle.py            python -m benchmarks.authoring_eval.oracle <case> <project-dir>
  audit_transcript.py  python -m benchmarks.authoring_eval.audit_transcript <transcript.jsonl> ...
  cases/<id>/
    prompt.md          the only text the subject sees
    oracle.json        the checks (hidden from the subject)
    fixtures/          files given to the subject with the prompt (only some cases)
    reference/         a good project; the positive test of the oracle (hidden)
  results/             short Markdown summaries of finished campaigns
```

Raw transcripts and run directories stay outside the repository.

## Cases

| Id | Class | Domain | What it tests |
|---|---|---|---|
| e01 | simple | flat dataset | count, unique id, closed value set, numeric range, generated text |
| e05 | simple | prices | closed value set, two ranges, one rule across two fields |
| e02 | complex | parent and child | exact count per parent, key copied from the parent, unique id over all children |
| e03 | complex | parent and child | child id built from the parent id, helper value that is not a field, fixed value |
| e04 | complex | CSV to JSON | comma separator, text to number, derived field, field subset, file output |

## Oracle checks

`oracle.json` holds a list of typed checks. Pydantic validates the list. The kinds are a closed set:
`build_ready`, `exact_count`, `unique`, `per_parent_count`, `fk_in_parent`, `value_in`, `range`,
`field_present`, `exact_fields`, `field_at_most`, `exact_rows`, `output_rows`.

The oracle copies the project to a private directory. It lays the case fixtures over the copy.
It then runs `Build` on the copy, runs the copy, and captures the rows per product.
Every check reads the captured rows. The verdict is JSON. It holds one short reason for each check and no row value.
The exit code is `0` when all checks pass and `1` otherwise.

Limits of the oracle:

- `per_parent_count` groups the child rows by the parent key. It does not prove that a child sits under the right parent when two parents swap keys.
- The oracle does not check how a value is built (for example that `slot_id` contains `depot_id`). It checks that the values are unique and complete.

## Protocol

Follow these steps for every run. One run is one sub-agent for one case.

1. Freeze the commit. Write the commit SHA in the results file.
2. Build the wheel: `uv build --wheel`.
3. Make a fresh virtual environment for the run: `uv venv <venv>` then `uv pip install --python <venv>/bin/python <wheel>`.
   Do not reuse a venv between runs.
4. Make an empty run directory outside the repository. Copy `cases/<id>/fixtures/` into it when the case has fixtures. Copy nothing else.
5. Start the sub-agent with the brief below. Use a fresh agent with no inherited turns. Record the model.
6. Wait for the agent notification. Record tokens, tool calls and duration from it.
7. Save the transcript outside the repository.
8. Run the oracle from the frozen checkout with its own venv, not the venv of the subject: `python -m benchmarks.authoring_eval.oracle <id> <run-dir>`. Record the verdict.
9. Run the audit: `python -m benchmarks.authoring_eval.audit_transcript <transcript> --allow <run-dir> --allow <venv> --forbid <repository-root>`.
   The harness saves long tool output in a `tool-results` directory under `~/.claude/projects/`. When the agent reads such a file, add that directory with `--allow`.
   Record the verdict.
10. Delete the run directory and the venv after the record is complete.

### Subject brief

Replace the words in angle brackets. Put no other text in the brief. Do not add hints.

```
Build the project that the task below describes.

Rules:
1. You may run only the installed `datamimic` command: <venv>/bin/datamimic.
2. Work only in this directory: <run-dir>. It is empty except for files that the task names.
3. Do not use the Skill tool.
4. Do not read any repository. Do not read any file named AGENTS.md.
5. Do not read or write any file outside <run-dir>.
6. Leave your finished project in <run-dir>.
7. Do not claim a result. An independent check decides.
8. Stop after <turn-limit> tool calls.

Task:
<contents of cases/<id>/prompt.md>
```

The turn limit is 40 tool calls for every case. A rule that the audit cannot check (rule 1, rule 8) is checked by reading the transcript.

### What to record for each run

| Field | Source |
|---|---|
| model | the agent setup |
| tokens, tool calls, duration | the agent notification |
| first Build call and its outcome | the transcript |
| final Build outcome | the `build_ready` check of the oracle |
| oracle verdict | the oracle output |
| audit verdict | the audit output |

A run is first-try `ready` when the first `datamimic authoring build` call of the agent returns `ready` and the oracle passes on the final project.
A run is a pass within the turn budget when the oracle passes on the final project and the agent used at most the turn limit.

### Void runs

A run is void when the audit finds a forbidden action. The forbidden actions are:

- any use of the `Skill` tool;
- any tool call that touches a path under the repository root;
- any mention of `AGENTS.md` in a tool call;
- any read or write of a file outside the run directory and the venv.

A void run does not count in any rate. Repeat it with a new agent. List the void runs in the results file with the finding.

The audit reads only the tool calls of the assistant. It reads shell commands for absolute and `~` paths only.
It does not resolve relative paths or paths built by variables. A void run can still pass the audit when the agent hides a path in a variable. Read the transcript when a result looks too good.

## Targets

| Class | Cases | Target |
|---|---|---|
| simple | e01, e05 | at least 95 % of runs are first-try `ready` and pass the oracle |
| complex | e02, e03, e04 | at least 80 % of runs pass the oracle within the turn budget |

Run every case with Haiku, Sonnet and Opus. Do at least five runs for each model and case.
Void runs do not count towards the five.

## Results

Write one short Markdown file for each campaign to `results/<date>-<commit>.md`:

1. the commit SHA and the wheel version;
2. one table: case, model, runs, first-try `ready`, oracle pass, void;
3. the failure classes, each with an issue number or a documented limit;
4. the void runs and their findings.

Do not commit raw transcripts, run directories or agent output.
