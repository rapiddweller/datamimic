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
datamimic validate <descriptor.xml>  # Validate XML descriptor and info.toml
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
  --target TEXT  Target directory for project creation
  --force       Force creation even if directory exists
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

#### `validate` - Validate Descriptor

```bash
datamimic validate <descriptor.xml>
```

The validate command performs the following checks:
- XML syntax validation
- Required elements and attributes
- Generate element structure
- Variable and key definitions
- info.toml validation (if present)
  - Required fields: projectName, description, dependencies, usage
  - Project name format
  - Field types

Example:

```bash
# Validate descriptor and info.toml
datamimic validate my-descriptor.xml
```

### Demo Management

#### `demo list` - List Available Demos

```bash
datamimic demo list
```

#### `demo create` - Create Demo Project

```bash
datamimic demo create [OPTIONS] [DEMO_NAME]

Options:
  --all          Create all available demos
  --target TEXT  Target directory for demo creation
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

- `DATAMIMIC_CONFIG`: Path to custom configuration file
- `DATAMIMIC_LOG_LEVEL`: Logging level (DEBUG|INFO|WARNING|ERROR)

## Exit Codes

The CLI uses the following exit codes:

- `0`: Success
- `1`: General error
- `2`: Invalid arguments
- `3`: Configuration error
- `4`: Runtime error

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
   - Verify info.toml required fields

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
