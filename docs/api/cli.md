# DATAMIMIC Command Line Interface (CLI)

The DATAMIMIC CLI provides a command-line interface for managing data generation projects and running descriptors.

## Installation

```bash
pip install datamimic-ce
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

XML is the persisted executable format. DM JSON is a transient representation;
Build expectations and roles are separate transaction input. See the
[worked transactions](../examples/authoring.md) and [migration](../migrations/authoring-errors.md).

```bash
datamimic authoring version
datamimic authoring schema [--name build_request_v4]
datamimic authoring capabilities [--full]
datamimic authoring capability --domain element --name generate
datamimic authoring reference [--topic overview] [--name <name>]
datamimic authoring compile <dm-json-input|-> [--descriptor-path model.xml]
datamimic authoring decompile <descriptor.xml|-> [--descriptor-path model.xml]
datamimic authoring build <build-request|-> [--workspace-root <project>]
datamimic authoring lint <descriptor.xml|->
datamimic authoring dry-run <descriptor.xml|-> [--max-count 10] [--sample-rows 5] [--timeout 30]
datamimic authoring run <descriptor.xml|-> [--allow-side-effects] [--max-count 10]
datamimic authoring export-contract <bundle.zip> [--package-version <version>] [--commit-sha <sha>]
```

Authoring defaults to `--format json`; `--format text` prints readable results.
Compile, decompile and Build return discriminated `ready`/`rejected` results.
Compilation readiness proves syntax only. Build additionally requires complete
bounded capture and acceptance; `verification` requests smoke/replay gates.
After a ready Build, persist `artifact.compiled_xml` and retain the separate proof.

File input uses its directory as the workspace. Stdin uses the current directory;
`--workspace-root` binds an explicit project root. Descriptor identities remain
project-relative. Bounded runs cap each generate instance; target isolation does
not certify an external write. Normal `datamimic run` keeps production semantics.

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
on stdout. Root `scaffold`, `lint`, `dry-run`, `reference`, and `capabilities` are
replaced by the typed subtree; old `--section`, `--fail-on`, and
`--max-diagnostics` options are retired.

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
