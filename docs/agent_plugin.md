# DATAMIMIC plugin for Codex and Claude Code

The plugin installs one shared `generate-test-data` skill: local CE authoring or
a connected Platform project, structured repair and correctly scoped proof.
It works in projects that do not contain DATAMIMIC's `AGENTS.md`.

## Install CE 5.0

Install CE from PyPI using Python 3.11+. From your own project:

```bash
python -m venv .venv
.venv/bin/python -m pip install datamimic-ce
.venv/bin/datamimic authoring reference --topic assembly --name starter
```

The response must contain a `version: "4.0"` starter transaction. A missing
`authoring` command means the wrong runtime is selected. Keep this project's
virtual environment active when starting the agent so it can resolve its CLI.
For an existing environment, use its dependency manager instead of replacing it.

## Codex

Register the repository marketplace, then install the plugin:

```bash
codex plugin marketplace add https://github.com/rapiddweller/datamimic.git
codex plugin add datamimic@datamimic
codex plugin list --marketplace datamimic --json
```

Open a new Codex session in your data project. Invoke `$generate-test-data`, or
ask for a synthetic dataset; the skill description allows automatic selection.
The repository marketplace also uses the Claude-compatible catalog supported by
Codex. The portable root manifest and Claude manifest share the same skill files.

## Claude Code

```bash
claude plugin marketplace add https://github.com/rapiddweller/datamimic.git
claude plugin install datamimic@datamimic
claude plugin details datamimic
```

Start a new session in your data project and invoke
`/datamimic:generate-test-data`.

## First task

```text
Create deterministic test data with DATAMIMIC in this project: four customers
with two orders each. Each order must copy its customer's actual identifier.
Verify the total and per-customer counts. Return the executable XML and bounded
proof; do not execute writes to external systems.
```

The skill reads the running contract, submits a Build, repairs diagnostics and
persists the returned XML only after readiness. It also returns a
[model review](../plugins/datamimic/skills/generate-test-data/references/review.md)
covering structure, key relationships, outputs and each original requirement.
Compile readiness proves syntax; Build
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
not a Python distribution. Native client validation and publication evidence
belong to the release issue. Public-directory submission is separate from
repository installation.
