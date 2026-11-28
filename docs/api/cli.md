# DATAMIMIC Command Line Interface (CLI)

The DATAMIMIC CLI provides a command-line interface for managing data generation projects and running descriptors.

## Installation

> **Pre-release.** CE 5.0 is not on PyPI yet. Until 5.0.0, install from GitHub `development`. Use Python 3.11 to 3.14.

```bash
python -m pip install "datamimic-ce @ git+https://github.com/rapiddweller/datamimic@development"
```

## Command Overview

### Basic Commands

```bash
datamimic version                    # Display version information
datamimic info                      # Show system and configuration details
datamimic init <project-name>       # Initialize a new project
datamimic run <descriptor.xml>      # Run a data generation descriptor
datamimic authoring lint <descriptor.xml>  # Validate persisted XML
datamimic authoring capabilities          # Compact typed CE vocabulary
```

### Demo Management

```bash
datamimic demo list                  # List available demos
datamimic demo create <demo-name>    # Create a specific demo
datamimic demo create --all          # Create all available demos
datamimic demo info <demo-name>      # Show detailed demo information
```

## Detailed Command Reference

### Project Management

#### `init` - Initialize a New Project

```bash
datamimic init <project-name> [OPTIONS]

Options:
  --target, -t TEXT  Target directory for project creation
  --force, -f        Force creation even if directory exists
```

Example:

```bash
# Create a new project in current directory
datamimic init my-data-project

# Create in specific location
datamimic init my-data-project --target /path/to/projects

# Force create even if exists
datamimic init my-data-project --force
```

#### `info` - System Information

```bash
datamimic info

Output includes:
- Python version
- DATAMIMIC version
- System information
- Configuration details
```

### Data Generation

#### `run` - Execute Data Generation

```bash
datamimic run <descriptor.xml> [OPTIONS]

Options:
  --platform-configs TEXT  Platform configurations in JSON format
  --task-id TEXT          Task identifier
  --test-mode             Run in test mode
```

Example:

```bash
# Basic usage
datamimic run my-descriptor.xml

# With task ID
datamimic run my-descriptor.xml --task-id task123

# In test mode
datamimic run my-descriptor.xml --test-mode
```

### Authoring

XML is the persisted executable format. A project is a directory with a
`datamimic.xml` entry and `acceptance/build.json` holding its expectations and roles.
DM JSON is a transient representation of one XML file. See the
[worked projects](../examples/authoring.md) and [migration](../migrations/authoring-errors.md).

```bash
datamimic authoring version
datamimic authoring schema [--name build_request_v5]
datamimic authoring capabilities [--full]
datamimic authoring capability --domain element --name generate
datamimic authoring reference [--topic overview] [--name <name>]
datamimic authoring compile <dm-json-input|-> [--descriptor-path model.xml]
datamimic authoring decompile <descriptor.xml|-> [--descriptor-path model.xml]
datamimic authoring build [<project>]
datamimic authoring lint <descriptor.xml|->
datamimic authoring dry-run <descriptor.xml|-> [--max-count 10] [--sample-rows 5] [--timeout 30]
datamimic authoring run <descriptor.xml|-> [--allow-side-effects] [--max-count 10]
datamimic authoring export-contract <bundle.tar.gz> [--package-version <version>] [--commit-sha <sha>]
```

`export-contract` writes a gzip-compressed tar archive. The archive contains
`manifest.json` and the JSON contract files. The output path does not change
the archive format.

#### Contract bundle compatibility

Every file in the bundle, including `manifest.json`, carries the same envelope:
`schema_version` (currently `"1"`, a single integer string) and `producer`
(`name`, `package_version`, `commit_sha`). `manifest.json` also lists a SHA-256
per file and `content_sha256` over all of them. The Build protocol
(`datamimic authoring version`, `build_protocol`) is versioned separately and
governs Build requests and results, not the bundle.

Compatible changes keep `schema_version` unchanged. A consumer must tolerate them:

- a new file in the bundle, a new top-level or nested JSON property;
- a new element, attribute, generator, rule, reference topic or schema id;
- a new value in an enum the bundle already lists, for example a new
  `ReferenceTopic`;
- changed descriptions, ordering of entries, hashes, `producer` values.

Breaking changes increment `schema_version` (`"1"` to `"2"`) and are named in the
release notes of the release that introduces them:

- removing or renaming a file, property, element, attribute or enum value;
- changing the type, required-ness or meaning of an existing property;
- changing the archive format or the manifest hash rule.

Consumer rules:

1. Read `manifest.json` first. Refuse a bundle whose `schema_version` is not one
   the consumer supports, and report the producer's `package_version`; do not
   guess at a newer layout.
2. Ignore properties and files you do not know. Do not validate bundle contents
   against a closed set of values; a value you do not know is new vocabulary,
   not corruption.
3. Treat an element, attribute or enum value you do not know as unsupported for
   that feature only (no completion, no diagnostics from it); do not fail the
   whole bundle.
4. Use `content_sha256` to decide whether a cached bundle is current, and
   the per-file hashes to detect a damaged file. `commit_sha` and
   `package_version` identify the producer; they are not compatibility signals.

Authoring commands default to `--format json`, except `export-contract`, which
prints its output path. For commands that support `--format`, `--format text`
prints readable results. `authoring init` prints the same `ProjectInitResult`
JSON as the MCP tool `datamimic_init`; its exit codes are the same in both formats.
Compile and decompile return discriminated `ready`/`rejected` results. Build
returns `ready`, `ready_with_gaps` (exit code 3: the run passed but open coverage
gaps remain; fix them before you report success), or `rejected` (exit code 1).
Compilation readiness proves syntax only. Build additionally requires complete
bounded capture and acceptance; `verification` requests smoke/replay gates.
A ready Build lists every project file it read with its digest (`artifact.files`);
changing any of them voids the proof.

Build takes the project directory as its workspace. Other file input uses its
directory as the workspace. Stdin uses the current directory;
`--workspace-root` binds an explicit project root. Descriptor identities remain
project-relative. Bounded runs cap each generate instance; target isolation does
not certify an external write. Normal `datamimic run` keeps production semantics.

Dry-run supports contained, literal XML includes directly under `setup`, including
nested descriptor dependencies. It checks the dependency graph before executing
and caps each freshly parsed product without rewriting your XML. Product names
must be literal and distinct. Dynamic paths, includes inside generators, cycles,
linked/escaping resources and unsupported operations are refused. Included contexts
retain the entry descriptor directory, as in normal execution.

Memstore reads across an include graph report `unknown` completeness until their
run-wide producer relationships are proven. Build still rejects external XML
includes; a successful raw dry-run is not a Build acceptance certificate.

### Demo Management

#### `demo list` - List Available Demos

```bash
datamimic demo list
```

#### `demo create` - Create Demo Project

```bash
datamimic demo create [OPTIONS] [DEMO_NAME]

Options:
  --all              Create all available demos
  --target, -t TEXT  Target directory for demo creation
  --overwrite, -o    Overwrite existing files if they exist
```

Example:

```bash
# Create specific demo
datamimic demo create demo-condition

# Create all demos
datamimic demo create --all --target ./demos
```

#### `demo info` - Demo Information

```bash
datamimic demo info <demo-name>

Output includes:
- Demo description
- Required dependencies
- Usage examples
- Configuration details
```

## Environment Variables

The CLI behavior can be customized using environment variables:

- `DATAMIMIC_CONFIG`: shown by `datamimic info`; not read by `run`
- `DATAMIMIC_OUTPUT_DIR`: Output directory shown by `datamimic info` (defaults to the current directory)
- `DATAMIMIC_LOG_LEVEL`: shown by `datamimic info`; `run` logs at INFO regardless

## Exit Codes

Most commands use `0` for success and `1` for a general error (e.g. `run` on a
missing descriptor, `init` on an invalid project name).

The `authoring` subtree uses `0` for success, `1` for rejected inputs or failed
operations, and `2` for CLI usage errors. Rejections are a single structured result
on stdout. Authoring operations live under `datamimic authoring`.

## Best Practices

1. **Project Organization**
   - Use descriptive project names
   - Maintain separate descriptors for different data domains
   - Version control your descriptors

2. **Performance**
   - Monitor memory usage with large generations
   - Configure output settings in your XML descriptor
   - Use appropriate data storage configuration

3. **Validation**
   - Always validate descriptors before running
   - Use the `info` command to verify system configuration
   - Check demo requirements before creation

4. **Error Handling**
   - Check validation errors carefully
   - Review XML syntax and structure
   - Use `--format json` to feed diagnostics into other tooling

## Troubleshooting

Common issues and solutions:

1. **Invalid Project Name**
   - Use alphanumeric characters and hyphens
   - Avoid special characters and spaces

2. **Descriptor Validation Fails**
   - Check XML syntax
   - Verify all required attributes
   - Ensure referenced entities exist

3. **Performance Issues**
   - Adjust batch size
   - Monitor system resources
   - Check output directory permissions

## Examples

### Complete Project Setup

```bash
# Initialize new project
datamimic init customer-data

# Create and lint descriptor
datamimic authoring lint customer-data/descriptor.xml

# Generate data
datamimic run customer-data/descriptor.xml
```

### Working with Demos

```bash
# List available demos
datamimic demo list

# Get demo details
datamimic demo info demo-condition

# Create and run demo
datamimic demo create demo-condition
datamimic run ./demo-condition/datamimic.xml
```

#### `authoring run-project` - Prove, Then Run a Project

```bash
datamimic authoring run-project <project> [--allow-side-effects] [--param NAME=VALUE]
```

`--param` follows the same rule as `run`: the first `=` separates, the name is a non-keyword Python identifier and
must not repeat. An invalid `--param` or `--timeout` exits `2` with a `not_run` result (`not_run_reason: input`).

Build runs first. A `not_run` result keeps the existing `outcome` and identifies
its cause with `not_run_reason`: `input`, `build_rejected`, or
`side_effects_not_allowed` (the enum also holds `confirmation_required`, which only the
MCP unverified run returns; `null` when execution occurred). Build warning
diagnostics, including open coverage gaps, are retained in the result. Review
`build_outcome` and `action_required` before reporting a successful run.

A passing Build puts its artifact in `build`, including the input digests in
`build.files`. A rejected Build returns its rejection in `build` instead. Each
listed output file carries its SHA-256 digest in `artifacts[].sha256` when readable.
Before and after execution, the runner compares the Build files against their
digests. `build_file_mismatches` lists any changed, missing or unreadable paths;
`[]` means both checks matched and `null` means no comparison was made.
