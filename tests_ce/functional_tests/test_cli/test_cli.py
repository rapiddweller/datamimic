from typer.testing import CliRunner

from datamimic_ce.cli import app

runner = CliRunner()

class TestCLI:
    def test_version_info(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "DATAMIMIC version:" in result.output

    def test_demo_list(self):
        result = runner.invoke(app, ["demo", "list"])
        assert result.exit_code == 0
        assert "Name" in result.output
        assert "Description" in result.output

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
            result = runner.invoke(app, [
                "demo", 
                "create", 
                demo_name, 
                "--target", 
                str(target_dir)
            ])

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
                import shutil
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