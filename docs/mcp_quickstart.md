# MCP server

The [agent plugin](agent_plugin.md) starts this server for you in Codex and Claude
Code: install the plugin and the `datamimic_*` tools appear. Use this page for a host
without the plugin, or to run the server yourself. The CLI works without it.

CE 5.0 is not on PyPI yet. Until 5.0.0, install it from GitHub `development` in a
Python 3.11 to 3.14 environment, with the MCP extra:

```bash
python -m pip install "datamimic-ce[mcp] @ git+https://github.com/rapiddweller/datamimic@development"
datamimic-mcp --transport stdio
```

Without a local environment, `uvx` runs the same command in an isolated one:

```bash
uvx --python ">=3.11,<3.15" --from "datamimic-ce[mcp] @ git+https://github.com/rapiddweller/datamimic@development" datamimic-mcp --transport stdio
```

Both transports use the same typed Authoring application. Every tool that works on
a project takes the required `project` argument: the absolute path of the directory
that holds `datamimic.xml`. A relative, missing or unusable path returns an `input`
diagnostic, not a tool error. `datamimic-mcp --workspace-root <dir>` only restricts
which projects a call may name; without it any project can be named. A project's
`.env` is read for that call only. `version`, `schema`, `capabilities` and
`capability` need no project. `reference`, codec, lint and bounded-run requests use
`{"request": {...}}` next to `project`. Follow each tool's advertised input schema.

| MCP tool | CLI equivalent |
|---|---|
| `datamimic_version` | `datamimic authoring version` |
| `datamimic_schema` | `datamimic authoring schema --name <name>` |
| `datamimic_capabilities` | `datamimic authoring capabilities` |
| `datamimic_capability` | `datamimic authoring capability --domain <domain> --name <name>` |
| `datamimic_reference` | `datamimic authoring reference --topic <topic> [--name <name>]` |
| `datamimic_compile` | `datamimic authoring compile -` |
| `datamimic_decompile` | `datamimic authoring decompile -` |
| `datamimic_init` | `datamimic authoring init <project> [--pattern flat]` |
| `datamimic_build` | `datamimic authoring build <project>` |
| `datamimic_lint` | `datamimic authoring lint -` |
| `datamimic_dry_run` | `datamimic authoring dry-run -` |
| `datamimic_run` | `datamimic authoring run -` |
| `datamimic_run_project` | `datamimic authoring run-project <project>` |
| `datamimic_run_project_unverified` | `datamimic run datamimic.xml` from the project directory |

`datamimic_version` also returns `build_protocol`; `5.0` is the Build contract this
documentation describes. Persist XML. `datamimic_init` writes the flat starter
(`datamimic.xml` and `acceptance/build.json`) that Build proves as `ready`; it creates a
missing project directory, never overwrites a file, and refuses a symlink or a path
outside the project with `outcome: not_written` and an `input` diagnostic. The flow
for a new project is `datamimic_init`, `datamimic_build`, `datamimic_run_project`.
`datamimic_build` proves a project: its
`datamimic.xml` against `acceptance/build.json`, which holds expectations,
`product_roles`, origin-tagged `acceptance_requirements` and smoke/replay options.
`datamimic_run_project` builds first and then produces the real data; it refuses a
project that reaches a database, MongoDB, a queue, object storage or `<execute>`
unless `allow_side_effects` is true. Compile/decompile readiness proves syntax; a
ready Build also carries bounded acceptance evidence. Target isolation does not prove
delivery to an external sink. A result over 60 000 characters is refused with a hint
that names the narrowing argument (for example `datamimic_capability` instead of the
full capability list). No schema resources or MCP-only compiler are registered.

For an explicitly authorized persistent operation that Build cannot prove, the
separate stdio-only `datamimic_run_project_unverified` tool runs the project without Build or
acceptance checks. It is not an automatic fallback for a rejected Build. Ask the
user to approve the unverified run and its persistent effects before setting both
`confirm_unverified` and `allow_side_effects` to `true`. This includes changes
inside the project and changes to external systems. A `completed` result means
only that the process exited successfully. Its `verification` is always
`not_verified`. Check the actual effects independently.
Failed or timed-out runs can leave partial effects. The execution log can contain
project data; share it only with authorized recipients.
If the result is too large, `details_truncated` is true and log lines and artifact
paths are omitted. The outcome and artifact count remain in the result.

## Codex

Add a stdio entry to Codex's MCP configuration:

```toml
[mcp_servers.datamimic_ce]
command = "/absolute/path/to/project/.venv/bin/datamimic-mcp"
args = ["--transport", "stdio"]
```

Run `codex mcp get datamimic_ce` and start a new session in that project.

## Claude Code

```bash
claude mcp add --transport stdio --scope local datamimic_ce -- \
  /absolute/path/to/project/.venv/bin/datamimic-mcp --transport stdio
claude mcp get datamimic_ce
```

In either client, list tools and call `datamimic_reference` with
`{"request": {"topic": "assembly", "name": "starter"}}` before authoring. For a
remote Platform project use its [HTTP/OAuth guide](https://docs.datamimic.io/advanced/connect-mcp-client/).

## SSE

```bash
datamimic-mcp --transport sse --host 127.0.0.1 --port 8765
```

`DATAMIMIC_MCP_API_KEY` enables `Authorization: Bearer <key>` or `X-API-Key: <key>`
for SSE. Stdio uses its owning process's access controls.

A `datamimic_run_project` result keeps `outcome` and reports why no execution
occurred in `not_run_reason` (`input`, `build_rejected`, or
`side_effects_not_allowed`; `null` after a run). Build warning diagnostics remain
in the result after execution.

Every execution of the project entry also leaves an audit record beside the project:
`docs/runs/<UTC start>_<task id>/` holds `run.json` (task id, actor, UTC start and end,
CE and Python version, parameter names without their values, the Build proof digests of
a verified run, outcome, exit code, written files) and `run.log` (the full log, not only
`log_tail`). The result names that folder in `record_path`; the task id is also the name
of the `output/<task id>/` folder. `docs/` is no Build input, so a record never opens a
coverage gap. When the record cannot be written, the run still ends normally, `record_path`
is `null` and a warning says so.
