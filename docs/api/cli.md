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
datamimic lint <descriptor.xml>     # Lint a descriptor: schema, semantics, best practices
datamimic validate <descriptor.xml>  # Validate XML descriptor (alias of lint)
datamimic capabilities               # Print the DSL surface as JSON (elements, generators, entities, converters, targets)
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

#### `lint` - Lint a Descriptor

```bash
datamimic lint <descriptor.xml> [OPTIONS]

Options:
  --format, -f TEXT      text | json (diagnostics v1) [default: text]
  --fail-on TEXT         error | warning [default: error]
  --max-diagnostics INT  [default: 200]
```

Runs the DSL linter (schema, semantic, and best-practice rule checks) against the
descriptor and prints diagnostics, each with a rule id (`DMxxx`), severity, and a
`fix_hint` describing what to change.

Exit codes: `0` when no diagnostic reaches the `--fail-on` threshold, `1` when one
does, `2` when the file is missing or the linter itself errors.

Example:

```bash
# Text output (default)
datamimic lint my-descriptor.xml

# JSON output for CI, capped at 50 diagnostics
datamimic lint my-descriptor.xml --format json --max-diagnostics 50
```

#### `validate` - Validate Descriptor (alias of `lint`)

```bash
datamimic validate <descriptor.xml>
```

`validate` is a thin alias for `lint` with fixed defaults
(`--format text --fail-on error --max-diagnostics 200`). It runs the same
schema/semantic/best-practice checks as `lint`; it does not read or validate
`info.toml`.

Example:

```bash
datamimic validate my-descriptor.xml
```

#### `capabilities` - Print the DSL Surface

```bash
datamimic capabilities
```

Prints a machine-readable JSON manifest of the DSL surface (elements,
aliases, generators, entities, converters, targets, distributions), derived live from the engine
registries so it cannot drift from the code. Useful for agents without an MCP
runtime; see the [MCP Quickstart](../mcp_quickstart.md) for the equivalent
`datamimic_reference` MCP tool.

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

`lint`/`validate` use a distinct, ESLint-style scheme:

- `0`: no diagnostic reached the `--fail-on` threshold
- `1`: at least one diagnostic reached the `--fail-on` threshold
- `2`: the descriptor file was not found, or the linter itself errored

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

# Create and validate descriptor
datamimic validate customer-data/descriptor.xml

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
