# DATAMIMIC Development Guidelines

## Build & Test Commands
- Format code: `uv run ruff format datamimic_ce`
- Lint code: `ruff check datamimic_ce`
- Type checking: `mypy datamimic_ce`
- Run all tests: `pytest tests_ce/`
- Run single test file: `pytest tests_ce/path/to/test_file.py`
- Run specific test: `pytest tests_ce/path/to/test_file.py::TestClass::test_method`
- Run with coverage: `pytest --cov=datamimic_ce tests_ce/`

## Code Style & Conventions
- Line length: 120 characters
- Python version: 3.11+
- Use Pydantic for data validation and configuration
- Maintain existing docstrings; only improve or expand
- Follow TDD approach for testing
- Modularize large files into smaller, cohesive modules
- Avoid using 'any' type; use explicit typing
- Use proper error handling with detailed error messages

## Project Structure
- Preserve existing directory structure and naming conventions
- Organize code by domain and functionality
- Test structure matches implementation (unit, functional, integration)
- XML-driven configuration is central to the architecture
- Follow entity-based architecture patterns

## Quality Guidelines
- All code must pass Ruff lint and Mypy type checks
- Tests should verify expected behavior before implementation
- Maintain high test coverage for all changes
- Document architectural decisions for clarity