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

    def test_validate_descriptor_failure(self):
        """Test failed XML descriptor validation"""
        with runner.isolated_filesystem():
            with open("invalid.xml", "w") as f:
                f.write("<invalid>")
            result = runner.invoke(app, ["validate", "invalid.xml"])
            assert result.exit_code == 1
            assert "validation failed" in result.output.lower()

    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file"""
        result = runner.invoke(app, ["validate", "nonexistent.xml"])
        assert result.exit_code == 1
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

    def test_run_with_environment_variables(self):
        """Test run command respects environment variables"""
        with (
            runner.isolated_filesystem(),
            patch.dict(os.environ, {"DATAMIMIC_CONFIG": "./config.yml"}),
        ):
            with open("test.xml", "w") as f:
                f.write("<setup></setup>")
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

    def test_run_executes_with_valid_descriptor(self):
        with runner.isolated_filesystem():
            with open("valid_descriptor.xml", "w") as f:
                f.write("<setup></setup>")
            result = runner.invoke(app, ["run", "valid_descriptor.xml"])
            assert result.exit_code == 0

    @patch("datamimic_ce.utils.file_util.FileUtil.create_project_structure")
    def test_init_creates_project_with_default_target(self, mock_create_structure, tmp_path):
        """Test project initialization in the current directory"""
        with runner.isolated_filesystem():
            project_name = "test-project"
            result = runner.invoke(app, ["init", project_name])

            project_dir = Path.cwd() / project_name
            try:
                assert result.exit_code == 0
                assert project_dir.exists(), "Project directory not created"
                mock_create_structure.assert_called_once_with(project_dir)
                assert "created successfully" in result.output
            finally:
                if project_dir.exists():
                    shutil.rmtree(project_dir)

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
