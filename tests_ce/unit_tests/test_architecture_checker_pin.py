"""Exercise CI checker provenance without installing or running ArchKeel."""

import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = Path("test-artifacts/architecture/ce-recursive-target")
ALTERNATE_VERSION = "9.8.7"
NATIVE_RECEIPT = '{"declared_rules":"FAIL","observation_complete":"UNKNOWN","exit_code":3}\n'


def step_run(name):
    workflow = (ROOT / ".github/workflows/main.yml").read_text(encoding="utf-8")
    step = workflow.split(f"      - name: {name}\n", 1)[1].split("\n      - name:", 1)[0]
    script = step.split("        run: ", 1)[1]
    return textwrap.dedent(script[2:]) if script.startswith("|\n") else script.strip()


@pytest.fixture
def checker(tmp_path):
    shutil.copyfile(ROOT / "Makefile", tmp_path / "Makefile")
    (tmp_path / "datamimic_ce").mkdir()
    stub = tmp_path / "uvx"
    stub.write_text(
        f"#!{sys.executable}\n"
        + textwrap.dedent(
            """\
            import json
            import os
            import sys
            from pathlib import Path

            args = sys.argv[1:]
            with Path("calls.jsonl").open("a") as log:
                log.write(json.dumps(args) + "\\n")
            if "archkeel" not in args:
                sys.exit(0)
            source = args[args.index("--from") + 1]
            version = os.environ.get("STUB_VERSION", source.removeprefix("archkeel=="))
            if "--version" in args:
                print("archkeel " + version)
            elif "report" in args:
                output = Path(args[args.index("--output") + 1])
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps({"producer_version": version}))
            elif "validate" in args:
                print(os.environ["NATIVE_RECEIPT"], end="")
                sys.exit(3)
            else:
                sys.exit(99)
            """
        ),
        encoding="utf-8",
    )
    stub.chmod(0o755)
    (tmp_path / "python").symlink_to(sys.executable)
    env = {
        **os.environ,
        "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"],
        "MAKEFLAGS": f"ARCHKEEL_SOURCE=archkeel=={ALTERNATE_VERSION}",
        "GITHUB_ENV": str(tmp_path / "github.env"),
        "NATIVE_RECEIPT": NATIVE_RECEIPT,
        "REPOSITORY": "rapiddweller/datamimic",
        "RUN_ID": "10",
        "RUN_ATTEMPT": "1",
        "HEAD_SHA": "a" * 40,
    }
    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@invalid", "commit", "--allow-empty", "-m", "test"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    return tmp_path, env


def test_alternate_pin_reaches_ci_metadata_report_and_native_validation(checker):
    directory, env = checker
    confirmed = subprocess.run(
        ["bash", "-e", "-c", step_run("Confirm pinned ArchKeel version")],
        cwd=directory,
        env=env,
        capture_output=True,
        text=True,
    )
    assert confirmed.returncode == 0, confirmed.stderr
    assert (directory / "github.env").read_text() == f"ARCHKEEL_VERSION={ALTERNATE_VERSION}\n"
    env.update(line.split("=", 1) for line in (directory / "github.env").read_text().splitlines())
    for name in ("Write report metadata", "Generate architecture report", "Capture native validation receipt"):
        result = subprocess.run(["bash", "-e", "-c", step_run(name)], cwd=directory, env=env, capture_output=True)
        assert result.returncode == (2 if name == "Capture native validation receipt" else 0), result.stderr
    output = directory / REPORT_DIR
    assert json.loads((output / "metadata.json").read_text())["archkeel_version"] == ALTERNATE_VERSION
    assert json.loads((output / "architecture.json").read_text())["producer_version"] == ALTERNATE_VERSION
    assert (output / "validation.json").read_text() == NATIVE_RECEIPT
    gate = subprocess.run(["make", "architecture-check"], cwd=directory, env=env, capture_output=True)
    assert gate.returncode != 0
    calls = [json.loads(line) for line in (directory / "calls.jsonl").read_text().splitlines()]
    checker_calls = [args for args in calls if "archkeel" in args]
    assert len(checker_calls) == 4
    assert all(args[args.index("--from") + 1] == f"archkeel=={ALTERNATE_VERSION}" for args in checker_calls)
    assert sum("validate" in args for args in checker_calls) == 2
    workflow = (ROOT / ".github/workflows/main.yml").read_text(encoding="utf-8")
    assert "ARCHKEEL_VERSION:" not in workflow
    assert "archkeel==" not in workflow


def test_stale_producer_cannot_write_checked_version_metadata(checker):
    directory, env = checker
    env["STUB_VERSION"] = "0.0.1"
    result = subprocess.run(
        ["bash", "-e", "-c", step_run("Confirm pinned ArchKeel version")],
        cwd=directory,
        env=env,
        capture_output=True,
    )
    assert result.returncode != 0
    assert not (directory / "github.env").exists()
    assert not (directory / REPORT_DIR / "metadata.json").exists()
