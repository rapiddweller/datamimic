# DATAMIMIC plugin for Codex and Claude Code

The plugin installs one shared `generate-test-data` skill: local CE authoring or
a connected Platform project, structured repair and correctly scoped proof.
It works in projects that do not contain DATAMIMIC's `AGENTS.md`.

## CE 5.0 source preview

CE 5.0 is not published yet. PyPI 4.3.0 has the previous authoring interface.
Use Python 3.11+ and a source checkout matching this guide. From your own project:

```bash
python -m venv .venv
.venv/bin/python -m pip install /absolute/path/to/datamimic
.venv/bin/datamimic authoring reference --topic assembly --name starter
```

The response must contain a `version: "4.0"` starter transaction. A missing
`authoring` command means the wrong runtime is selected. Keep this project's
virtual environment active when starting the agent so it can resolve its CLI.
For an existing environment, use its dependency manager instead of replacing it.

## Codex

Register this checkout's repository marketplace, then install the plugin:

```bash
codex plugin marketplace add /absolute/path/to/datamimic
codex plugin add datamimic@datamimic
codex plugin list --marketplace datamimic --json
```

Open a new Codex session in your data project. Invoke `$generate-test-data`, or
ask for a synthetic dataset; the skill description allows automatic selection.
The repository marketplace also uses the Claude-compatible catalog supported by
Codex. The portable root manifest and Claude manifest share the same skill files.

## Claude Code

```bash
claude plugin marketplace add /absolute/path/to/datamimic
claude plugin install datamimic@datamimic
claude plugin details datamimic
```

Start a new session in your data project and invoke
`/datamimic:generate-test-data`. For a session-only test, run
`claude --plugin-dir /absolute/path/to/datamimic/plugins/datamimic` there.

## First task

```text
Create deterministic test data with DATAMIMIC in this project: four customers
with two orders each. Each order must copy its customer's actual identifier.
Verify the total and per-customer counts. Return the executable XML and bounded
proof; do not execute writes to external systems.
```

The skill reads the running contract, submits a Build, repairs diagnostics and
persists the returned XML only after readiness. It checks the result against
the original requested requirements. Compile readiness proves syntax; Build
readiness additionally proves bounded acceptance. External delivery requires its
own execution and readback.

An optional [local CE MCP connection](mcp_quickstart.md) exposes the same service.
For a remote Platform project, use its existing project MCP connection and server
instructions. Its Pending/Ready/commit lifecycle and file references remain
server-owned; local XML writes do not update that project.

## Maintainers

```bash
make agent-plugin-check
make agent-plugin-package
claude plugin validate --strict plugins/datamimic
claude plugin validate --strict .
```

The ZIP is a separate `test-artifacts/agent-plugin/datamimic.zip` artifact; it is
not a Python distribution. The [5.0 checklist](releases/5.0.md) tracks native
client evidence and publication. Public-directory submission is separate from
repository installation.
