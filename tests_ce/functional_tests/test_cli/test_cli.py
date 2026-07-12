import json
import os
import shutil
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from datamimic_ce.cli import app

runner = CliRunner()


class TestCLI:
    def test_version_info(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "DATAMIMIC version:" in result.output

    def test_info_command(self):
        """Test info command shows system and configuration details"""
        result = runner.invoke(app, ["info"])
        assert result.exit_code == 0
        assert "System Information" in result.output
        assert "DATAMIMIC Version" in result.output
        assert "Python Version" in result.output
        assert "Operating System" in result.output
        assert "Config File" in result.output
        assert "Log Level" in result.output

    def test_validate_descriptor_failure(self, tmp_path, monkeypatch):
        """A broken descriptor lints with findings (validate is an alias of lint): exit 1."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "invalid.xml").write_text("<invalid>")
        result = runner.invoke(app, ["validate", "invalid.xml"])
        assert result.exit_code == 1
        assert "error" in result.output.lower()  # DM001 XML-not-well-formed

    def test_validate_nonexistent_file(self):
        """A missing file is an operational error, not a finding: exit 2 (ESLint convention)."""
        result = runner.invoke(app, ["validate", "nonexistent.xml"])
        assert result.exit_code == 2
        assert "file not found" in result.output.lower()

    def test_demo_list(self):
        result = runner.invoke(app, ["demo", "list"])
        assert result.exit_code == 0
        assert "Name" in result.output
        assert "Description" in result.output

    def test_demo_info_valid(self):
        """Test getting information about a valid demo"""
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch(
                "toml.load",
                return_value={
                    "projectName": "Test Demo",
                    "description": "A test demo",
                    "dependencies": "pytest",
                    "usage": "datamimic demo create test-demo",
                },
            ),
        ):
            result = runner.invoke(app, ["demo", "info", "test-demo"])
            assert result.exit_code == 0
            assert "Test Demo" in result.output
            assert "A test demo" in result.output
            assert "pytest" in result.output

    def test_demo_info_invalid(self):
        """Test getting information about an invalid demo"""
        result = runner.invoke(app, ["demo", "info", "nonexistent-demo"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_run_with_environment_variables(self, tmp_path, monkeypatch):
        """Test run command respects environment variables"""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "test.xml").write_text("<setup></setup>")
        with patch.dict(os.environ, {"DATAMIMIC_CONFIG": "./config.yml"}):
            result = runner.invoke(app, ["run", "test.xml"])
            assert result.exit_code == 0

    def test_demo_create_requires_demo_name_or_all(self):
        result = runner.invoke(app, ["demo", "create"])
        assert result.exit_code == 1
        assert "Please specify a demo name or use '--all' to create all demos." in result.output

    def test_demo_create_all_requires_target_directory(self):
        result = runner.invoke(app, ["demo", "create", "--all"])
        assert result.exit_code == 1
        assert "Target directory is required when using '--all'." in result.output

    def test_demo_create_specific_demo(self, tmp_path):
        # Setup
        demo_name = "demo-condition"
        target_dir = tmp_path / demo_name

        try:
            # Execute
            result = runner.invoke(app, ["demo", "create", demo_name, "--target", str(target_dir)])

            # Verify
            assert result.exit_code == 0
            assert target_dir.exists(), "Demo directory not created"
            assert (target_dir / "datamimic.xml").exists(), "Descriptor file missing"

            # Verify content
            descriptor_content = (target_dir / "datamimic.xml").read_text()
            assert "<setup>" in descriptor_content, "Invalid descriptor content"

        finally:
            # Cleanup
            if target_dir.exists():
                shutil.rmtree(target_dir)

    def test_run_requires_valid_descriptor_path(self):
        result = runner.invoke(app, ["run", "invalid_descriptor.xml"])
        assert result.exit_code == 1
        assert "Invalid descriptor file path:" in result.output

    def test_run_executes_with_valid_descriptor(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "valid_descriptor.xml").write_text("<setup></setup>")
        result = runner.invoke(app, ["run", "valid_descriptor.xml"])
        assert result.exit_code == 0

    @patch("datamimic_ce.utils.file_util.FileUtil.create_project_structure")
    def test_init_creates_project_with_default_target(self, mock_create_structure, tmp_path, monkeypatch):
        """Test project initialization in the current directory"""
        monkeypatch.chdir(tmp_path)
        project_name = "test-project"
        result = runner.invoke(app, ["init", project_name])

        project_dir = tmp_path / project_name
        assert result.exit_code == 0
        assert project_dir.exists(), "Project directory not created"
        mock_create_structure.assert_called_once_with(project_dir)
        assert "created successfully" in result.output

    @patch("datamimic_ce.utils.file_util.FileUtil.create_project_structure")
    def test_init_creates_project_with_custom_target(self, mock_create_structure, tmp_path):
        """Test project initialization with a custom target directory"""
        project_name = "test-project"
        target_dir = tmp_path / "custom-location"

        try:
            result = runner.invoke(app, ["init", project_name, "--target", str(target_dir)])

            project_path = target_dir / project_name
            assert result.exit_code == 0
            assert project_path.exists(), "Project directory not created"
            mock_create_structure.assert_called_once_with(project_path)
            assert "created successfully" in result.output
        finally:
            if target_dir.exists():
                shutil.rmtree(target_dir)

    @patch("datamimic_ce.utils.file_util.FileUtil.create_project_structure")
    def test_init_creates_nested_directories(self, mock_create_structure, tmp_path):
        """Test project initialization with nested directory structure"""
        project_name = "test-project"
        target_dir = tmp_path / "deep/nested/location"

        try:
            result = runner.invoke(app, ["init", project_name, "--target", str(target_dir)])

            project_path = target_dir / project_name
            assert result.exit_code == 0
            assert project_path.exists(), "Nested project directory not created"
            mock_create_structure.assert_called_once_with(project_path)
        finally:
            if target_dir.exists():
                shutil.rmtree(target_dir)

    @patch("datamimic_ce.utils.file_util.FileUtil.create_project_structure")
    def test_init_with_existing_directory(self, mock_create_structure, tmp_path):
        """Test project initialization in an existing directory"""
        project_name = "existing-project"
        project_dir = tmp_path / project_name
        project_dir.mkdir(parents=True)

        try:
            result = runner.invoke(app, ["init", project_name, "--target", str(tmp_path)])

            assert result.exit_code == 1  # Should fail without force option
            assert "already exists" in result.output
            mock_create_structure.assert_not_called()
        finally:
            if project_dir.exists():
                shutil.rmtree(project_dir)

    @patch("datamimic_ce.utils.file_util.FileUtil.create_project_structure")
    def test_init_with_force_option(self, mock_create_structure, tmp_path):
        """Test initialization with force option on existing directory"""
        project_name = "existing-project"
        project_dir = tmp_path / project_name
        project_dir.mkdir(parents=True)

        try:
            result = runner.invoke(app, ["init", project_name, "--target", str(tmp_path), "--force"])

            assert result.exit_code == 0
            assert project_dir.exists()
            mock_create_structure.assert_called_once_with(project_dir)
            assert "created successfully" in result.output
        finally:
            if project_dir.exists():
                shutil.rmtree(project_dir)

    def test_init_with_invalid_project_name(self):
        """Test initialization with invalid project name"""
        result = runner.invoke(app, ["init", "invalid/name"])
        assert result.exit_code == 1
        assert "Error: Project name can only contain" in result.output

    def test_demo_info(self):
        """Test getting detailed information about a specific demo"""
        result = runner.invoke(app, ["demo", "info", "demo-condition"])
        assert result.exit_code == 0
        assert "Demo Information" in result.output
        assert "Description" in result.output
        assert "Required Dependencies" in result.output

    # Tests for dry-run command
    def test_dry_run_nonexistent_file(self):
        """A missing descriptor file for dry-run is an operational error: exit 2."""
        result = runner.invoke(app, ["dry-run", "nonexistent.xml"])
        assert result.exit_code == 2
        assert "file not found" in result.output.lower()

    def test_dry_run_valid_descriptor_json(self, tmp_path, monkeypatch):
        """A valid descriptor dry-run succeeds and outputs JSON with ok=true and products,
        with count (25) above the default --max-count (10)/--sample-rows (5) to actually
        exercise the capping behavior the command's help text advertises."""
        monkeypatch.chdir(tmp_path)
        descriptor_content = """<setup rngSeed="1">
    <generate name="test" count="25" target="">
        <key name="id" generator="IncrementGenerator"/>
    </generate>
</setup>"""
        (tmp_path / "test.xml").write_text(descriptor_content)
        result = runner.invoke(app, ["dry-run", "test.xml", "--format", "json"])
        assert result.exit_code == 0
        output_json = json.loads(result.output)
        assert output_json["ok"] is True
        assert len(output_json["products"]) > 0
        product = output_json["products"][0]
        assert product["name"] == "test"
        assert product["count"] == 10  # capped at default --max-count
        assert len(product["sample"]) == 5  # capped at default --sample-rows
        assert product["truncated_rows"] is True

    def test_dry_run_lint_failure(self, tmp_path, monkeypatch):
        """A broken descriptor (invalid XML) fails dry-run at the lint gate with exit 1."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "invalid.xml").write_text("<invalid>")
        result = runner.invoke(app, ["dry-run", "invalid.xml"])
        assert result.exit_code == 1
        assert "DM001" in result.output
        assert "stage: lint" in result.output

    # Tests for reference command
    def test_reference_overview(self):
        """Reference overview command returns the DSL cheatsheet."""
        result = runner.invoke(app, ["reference", "overview"])
        assert result.exit_code == 0
        assert "# DATAMIMIC DSL" in result.output
        assert "## Minimal descriptor" in result.output
        assert '<setup rngSeed=' in result.output

    def test_reference_element_variable(self):
        """Reference element command with variable tag returns its real attribute schema."""
        result = runner.invoke(app, ["reference", "element", "variable"])
        assert result.exit_code == 0
        assert "# <variable>" in result.output
        assert "name: str (required)" in result.output
        assert "Allowed inside:" in result.output

    def test_reference_element_missing_name(self):
        """Reference element command without name fails with the specific fix-hint message."""
        result = runner.invoke(app, ["reference", "element"])
        assert result.exit_code == 1
        assert "topic=element needs name" in result.output

    def test_reference_unknown_topic(self):
        """Reference command with unknown topic fails with the specific unknown-topic message."""
        result = runner.invoke(app, ["reference", "bogus-topic-xyz"])
        assert result.exit_code == 1
        assert "Unknown topic 'bogus-topic-xyz'" in result.output
