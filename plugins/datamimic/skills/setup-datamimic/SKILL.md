---
name: setup-datamimic
description: Use when the DATAMIMIC tools of this plugin are not connected, to start them or to set up local DATAMIMIC authoring in a project.
---

# Set up DATAMIMIC

The plugin starts a DATAMIMIC server through `uvx`. This skill makes sure that
`uvx` works, warms the server once and checks the contract. A connected Platform
project uses its existing remote service and needs none of this.

## Connect the server

1. Check `uvx`: `command -v uvx` (Windows: `where uvx`). If it is missing, tell the
   user in one line: "Install uv to connect the DATAMIMIC tools:
   https://docs.astral.sh/uv/". Do not install uv or any system tool yourself.
   Then use the fallback below.
2. Read the server entry in `../../.mcp.json` (relative to this skill's directory).
   Its `args` hold the Python range after `--python` and the install reference
   after `--from`. Use exactly those values; do not copy them anywhere else.
3. Warm the server once. The first start builds an isolated environment and can
   take minutes; a later start takes seconds:

   ```bash
   uvx --python "<range>" --from "<install reference>" datamimic-mcp --help
   ```

4. Ask the user to reconnect the server (Claude Code: `/mcp`, then reconnect; Codex:
   restart the session). If the tools are still missing, report the exact output of
   the warm-up command.
5. Call `datamimic_version`. It must show `build_protocol` `5.0`. Another value
   or a missing field means this package is too old for the plugin: report it.

To update to the newest `development` commit, run the warm-up command again with
`uvx --refresh`:

```bash
uvx --refresh --python "<range>" --from "<install reference>" datamimic-mcp --help
```

Then reconnect the server.

## Without uv

Use the project's own CLI environment. Read the project's instructions, Makefile,
dependency declarations and lockfile; use its configured Python 3.11+ interpreter
and dependency manager and preserve its pins. If no environment is configured, create
`.venv` in the project with a Python 3.11+ interpreter's `-m venv .venv`. If Python
is unavailable, report that prerequisite; do not install a system interpreter.

Try the environment's `datamimic authoring version`. A compatible runtime shows
`build_protocol` `5.0`; then setup is complete and no install is needed. Otherwise
install the package from the install reference you read in step 2, using the
environment's interpreter directly:

```bash
python -m pip install "<install reference>"
```

Here `python` means the absolute selected interpreter, and `<install reference>`
is the string after `--from` in `../../.mcp.json`. An existing incompatible
explicit pin is a reported dependency conflict: do not remove it. If the
installation fails, report the stage and the exact error and leave the project
unchanged. Check `datamimic authoring version` again, then continue the data task
with [CE authoring](../generate-test-data/references/ce.md).
