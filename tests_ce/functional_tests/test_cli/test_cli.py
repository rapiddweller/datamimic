import json
import os
import shutil
import shlex
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from typer.testing import CliRunner

from datamimic_ce.interfaces.cli import app
from datamimic_ce.interfaces.cli.presenter import emit_project_created
from datamimic_ce.interfaces.project import project_scaffold

runner = CliRunner()


class TestCLI:
    def test_init_creates_project_structure(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["init", "sample-project"])

        project_dir = tmp_path / "sample-project"
        assert result.exit_code == 0
        assert all((project_dir / name).is_dir() for name in ("data", "output", "script", "config"))
        assert (project_dir / "datamimic.xml").is_file()
        assert (project_dir / "README.md").is_file()
        assert (project_dir / "acceptance/build.json").is_file()
        assert f"cd {shlex.quote(str(project_dir))}" in result.output.replace("\n", "")
        build = runner.invoke(app, ["authoring", "build", str(project_dir)])
        assert build.exit_code == 0, build.output
        assert json.loads(build.output)["outcome"] == "ready"
        acceptance_path = project_dir / "acceptance/build.json"
        acceptance = json.loads(acceptance_path.read_text())
        acceptance["expectations"][0]["count"] += 1
        acceptance_path.write_text(json.dumps(acceptance))
        rejected = runner.invoke(app, ["authoring", "build", str(project_dir)])
        assert rejected.exit_code == 1, rejected.output
        assert json.loads(rejected.output)["outcome"] == "rejected"

    def test_init_target_and_force_reports_only_overwrites(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        target = tmp_path / "target with spaces"
        project = target / "sample"
        project.mkdir(parents=True)
        (project / "datamimic.xml").write_text("old")
        (project / "keep.txt").write_text("keep")
        expected_overwritten = {
            str(file.path) for file in project_scaffold("sample").files if (project / file.path).is_file()
        }
        result = runner.invoke(app, ["init", "sample", "--target", str(target), "--force"])
        assert result.exit_code == 0, result.output
        output = result.output.replace("\n", "")
        assert f"cd {shlex.quote(str(project))}" in output
        assert "Overwritten:" in output and "datamimic.xml" in output
        reported = next(
            line.removeprefix("Overwritten: ")
            for line in result.output.splitlines()
            if line.startswith("Overwritten: ")
        )
        assert set(reported.split(", ")) == expected_overwritten
        assert "README.md" not in output and "acceptance/build.json" not in output
        assert (project / "keep.txt").read_text() == "keep"
        assert "acceptance/build.json" in (project / "README.md").read_text()
        help_result = runner.invoke(app, ["init", "--help"])
        assert "starter files" in help_result.output
        again = runner.invoke(app, ["init", "sample", "--target", str(target), "--force"])
        assert again.exit_code == 0, again.output
        assert all(name in again.output for name in ("datamimic.xml", "README.md", "acceptance/build.json"))

    def test_init_force_fails_clearly_when_a_starter_path_is_a_directory(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "sample" / "acceptance" / "build.json").mkdir(parents=True)
        result = runner.invoke(app, ["init", "sample", "--force"])
        assert result.exit_code == 1
        assert "is not a file" in result.output and "Traceback" not in result.output
        assert result.exception is None or isinstance(result.exception, SystemExit)

    def test_init_force_refusal_writes_nothing(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        project = tmp_path / "sample"
        project.mkdir()
        (project / "datamimic.xml").write_bytes(b"<setup>original</setup>")
        (project / "acceptance").write_text("a regular file")
        result = runner.invoke(app, ["init", "sample", "--force"])
        assert result.exit_code == 1
        assert "acceptance" in result.output and "not a directory" in result.output
        assert (project / "datamimic.xml").read_bytes() == b"<setup>original</setup>"
        assert not (project / "README.md").exists() and not (project / "data").exists()

    @pytest.mark.skipif(not hasattr(os, "symlink") or os.name == "nt", reason="needs symlink support")
    def test_init_force_refuses_a_symlinked_starter_directory(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        project = tmp_path / "sample"
        project.mkdir()
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        (project / "acceptance").symlink_to(elsewhere, target_is_directory=True)
        result = runner.invoke(app, ["init", "sample", "--force"])
        assert result.exit_code == 1
        assert "symlink" in result.output
        assert not (project / "data").exists() and not (project / "datamimic.xml").exists()
        assert not any(elsewhere.iterdir())

    @pytest.mark.parametrize(
        ("os_name", "expected"),
        [("posix", "cd '/tmp/my project' &&"), ("nt", 'cd "/tmp/my project" &&')],
    )
    def test_next_step_hint_quotes_for_the_shell(self, monkeypatch, capsys, os_name, expected):
        monkeypatch.setattr("datamimic_ce.interfaces.cli.presenter.os", SimpleNamespace(name=os_name))
        emit_project_created("p", Path("/tmp/my project"), ())
        assert expected in capsys.readouterr().out

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

    def test_demo_list(self):
        result = runner.invoke(app, ["demo", "list"])
        assert result.exit_code == 0
        assert "Name" in result.output
        assert "Description" in result.output

    def test_demo_info_valid(self):
        """Test getting information about a valid demo"""
        with (
            patch("pathlib.Path.is_file", return_value=True),
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
        assert "Specify a demo name or use --all" in result.output

    def test_demo_create_all_requires_target_directory(self):
        result = runner.invoke(app, ["demo", "create", "--all"])
        assert result.exit_code == 1
        assert "Target directory is required with --all" in result.output

    def test_demo_create_all_has_descriptors_for_discovered_demos(self, tmp_path):
        from datamimic_ce.interfaces.demo import demo_autocomplete
        from datamimic_ce.resources.api import demo_names

        names = set(demo_names())
        assert names
        assert "demo-clinical-trial" not in names
        assert list(demo_autocomplete("demo-clinical-trial")) == []

        result = runner.invoke(app, ["demo", "create", "--all", "--target", str(tmp_path)])

        assert result.exit_code == 0, result.output
        created = {path.name for path in tmp_path.iterdir() if path.is_dir()}
        assert created == names
        assert all((tmp_path / name / "datamimic.xml").is_file() for name in created)

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

    @patch("datamimic_ce.interfaces.cli.runtime.create_project_structure")
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

    @patch("datamimic_ce.interfaces.cli.runtime.create_project_structure")
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

    @patch("datamimic_ce.interfaces.cli.runtime.create_project_structure")
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

    @patch("datamimic_ce.interfaces.cli.runtime.create_project_structure")
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

    @patch("datamimic_ce.interfaces.cli.runtime.create_project_structure")
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

    # Tests for reference command

    # Tests for scaffold command
    def _run_scaffold(self, tmp_path, monkeypatch, spec_or_text, *extra_args, filename="spec.json"):
        monkeypatch.chdir(tmp_path)
        text = spec_or_text if isinstance(spec_or_text, str) else json.dumps(spec_or_text)
        (tmp_path / filename).write_text(text)
        return runner.invoke(app, ["scaffold", filename, *extra_args])

    # Tests for Defect 4: scaffold missing-file with --format json emits single JSON document

    # Tests for Defect 5: dry-run format validation and JSON error paths
    # Output should be text, not JSON (format validation happens before any engine activity)
