---
name: setup-datamimic
description: Use when setting up local DATAMIMIC authoring in a project, or when its CE CLI is missing or incompatible.
---

# Set up DATAMIMIC in the project

Prepare the selected local project for CE authoring, then continue the user's
data task. A connected Platform project uses its existing remote service and
does not need a local CE installation.

## Select the environment

Read the project's instructions, Makefile, dependency declarations and lockfile.
Use its configured Python interpreter and dependency manager. Resolve absolute
project and interpreter paths; a global CLI on PATH is not evidence that it
belongs to this project. Preserve the existing environment and dependencies.

If no environment is configured, find Python 3.11+ and create `.venv` in the
project with that interpreter's `-m venv .venv`. Keep model resources outside
root `.venv`/`venv` directories, which bounded snapshots exclude. Use the
environment's binaries explicitly, including `Scripts` on Windows. If Python is unavailable, report
that prerequisite; do not install a system interpreter.

## Install only when needed

Try the selected environment's `datamimic authoring version` and
`datamimic authoring reference --topic assembly --name starter`. A compatible
CE 5 runtime must expose Build protocol `5.0`: a starter with `entry_xml` and an
`acceptance` carrying expectations.
If that contract is already available, setup is complete: record the resolved
paths/version and continue the data task. Do not invoke pip or another dependency
manager, even to request an already satisfied package.

Only if CE is absent or incompatible, install the published CE 5 dependency through
the project's dependency manager and record it in the existing dependency/lock
files. For an unmanaged virtual environment, use its Python directly:

```bash
python -m pip install "datamimic-ce>=5.0.0,<6"
```

Here `python` means the absolute selected environment interpreter. Complete this
setup as part of the requested task; do not send the user a command to run when
you can execute it. Respect host permissions. An existing incompatible explicit
pin needs a reported dependency conflict, not silently removing the pin or
replacing the environment. CLI authoring needs no MCP extra.

If the published version cannot be resolved, installation fails, or the live
contract remains incompatible, preserve the project and report the exact stage
and error. Do not substitute an old API, source checkout or local wheel. An
access/configuration failure is not an authoring result.

## Verify and continue

Run both discovery commands with the installed project's absolute CLI. Check
the actual returned contract; installation exit status alone is insufficient.
Record the project root, interpreter, CLI path, CE version and any dependency
changes. A second invocation should reuse the verified environment unchanged.
Return to the original data task using [CE authoring](../generate-test-data/references/ce.md).
