# DATAMIMIC plugin for Codex and Claude Code

The plugin provides shared setup and `generate-test-data` skills: local CE
authoring or a connected Platform project, structured repair and scoped proof.
It works in projects that do not contain DATAMIMIC's `AGENTS.md`.

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
Run the offered setup workflow, or start your data task; local authoring invokes
the same setup when needed.

## Claude Code

```bash
claude plugin marketplace add https://github.com/rapiddweller/datamimic.git
claude plugin install datamimic@datamimic
claude plugin details datamimic
```

Start a new session in your data project and invoke
`/datamimic:generate-test-data`. Setup also has an explicit entry:
`/datamimic:setup-datamimic`.

## Automatic project setup

The shared [setup skill](../plugins/datamimic/skills/setup-datamimic/SKILL.md)
uses the project's Python 3.11+ environment and dependency manager. If CE is
missing or incompatible, it installs published `datamimic-ce>=5.0.0,<6` from
PyPI, checks the live authoring contract and continues your original task.
An already compatible environment is reused. Existing dependency conflicts are
reported rather than silently replacing pins. A connected Platform project uses
its remote service and needs no local CE install.

For manual CLI installation, use your project environment:

```bash
python -m pip install "datamimic-ce>=5.0.0,<6"
```

The optional MCP transport has its own [registration guide](mcp_quickstart.md).
Setup does not automatically configure it.

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
The executable project itself keeps field operations and rule parameters visible;
Python functions have explicit inputs, outputs and a justified algorithmic role.
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

The [LBA reference evaluation](evaluations/lba-authoring.md) defines the complex
model-quality gate and records the distinction between EE evidence and CE proof.
