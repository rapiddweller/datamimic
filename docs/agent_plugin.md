# DATAMIMIC plugin for Codex and Claude Code

The plugin provides shared setup and `generate-test-data` skills and a local CE
server: local CE authoring or a connected Platform project, structured repair and
scoped proof.
It works in projects that do not contain DATAMIMIC's `AGENTS.md`.

## What the install connects

One install gives the agent the skills and a local DATAMIMIC server (`datamimic_*`
tools, server name `datamimic`). The server starts through `uvx` from the plugin's
[`.mcp.json`](../plugins/datamimic/.mcp.json). Until CE 5.0 is released, that file
installs the package from the GitHub branch `development`; after the release it
names the published `datamimic-ce[mcp]>=5.0.0,<6`. It is the only file that holds
the install reference.

Requirements: [uv](https://docs.astral.sh/uv/) on the PATH. `uvx` picks a Python
from `>=3.11,<3.15` by itself; it does not use your project's virtual environment.
The tools take the absolute path of the data project (the directory that holds
`datamimic.xml`) on every call, so the server works from any start directory.

## Codex

Register the repository marketplace, then install the plugin:

```bash
codex plugin marketplace add https://github.com/rapiddweller/datamimic.git
codex plugin add datamimic@datamimic
codex plugin list --marketplace datamimic --json
```

Open a new Codex session in your data project. Invoke `$generate-test-data`, or
ask for a synthetic dataset; the skill description allows automatic selection.
Codex reads the Claude-compatible catalog in `.claude-plugin/marketplace.json` and the
plugin's `.codex-plugin/plugin.json`, which points to the same skills and `.mcp.json`.
`codex mcp list` does not show servers that a plugin provides.

## Claude Code

```bash
claude plugin marketplace add https://github.com/rapiddweller/datamimic.git
claude plugin install datamimic@datamimic
claude plugin details datamimic
```

`claude plugin details` lists the MCP server `datamimic`. Start a new session in your
data project and invoke `/datamimic:generate-test-data`. Setup also has an explicit
entry: `/datamimic:setup-datamimic`.

## First start

The first start of the server builds an isolated environment and clones the
repository. Measured on one machine (uv 0.12.3, Python 3.11, other packages already
cached): the first start took 7 s, a later start 1 s. With an empty uv cache expect
minutes. Claude Code can show the server as failed or pending in `/mcp` until that
build ends; Codex waits up to 300 s. The skills load in both cases.

The [setup skill](../plugins/datamimic/skills/setup-datamimic/SKILL.md) warms the
server once with `uvx ... datamimic-mcp --help`, asks you to reconnect, and checks
that `datamimic_version` shows `build_protocol` `5.0`; for a git install it also shows the `commit`. New commits on `development`
arrive only after `uvx --refresh` with the same arguments, then a reconnect.

Without uv the server does not start; the skills still load. The setup skill then
installs the same package reference into the project's environment and the agent uses
the CLI. Install uv to connect the tools: https://docs.astral.sh/uv/.

For manual CLI installation, use your project environment and the reference from
`.mcp.json`:

```bash
python -m pip install "datamimic-ce[mcp] @ git+https://github.com/rapiddweller/datamimic@development"
```

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

The [MCP quickstart](mcp_quickstart.md) describes the server for other hosts.
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

The [complex reference evaluation](evaluations/complex-authoring-reference.md) defines the complex
model-quality gate and records the distinction between EE evidence and CE proof.
