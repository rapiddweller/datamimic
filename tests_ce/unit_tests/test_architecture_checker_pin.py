"""Exercise CI checker provenance without installing or running ArchKeel."""

import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(os.name == "nt", reason="Exercises the Ubuntu Bash/Make workflow")

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = Path("test-artifacts/architecture/ce-recursive-target")
ALTERNATE_REVISION = "a" * 40


def receipt(verdict, exit_code):
    return (
        json.dumps(
            {
                "outcome": "verdict",
                "status": verdict,
                "exit_code": exit_code,
                "frame": {"rules": {"example": ["kind", verdict]}, "violations": {}},
            }
        )
        + "\n"
    )


def step_run(name):
    workflow = (ROOT / ".github/workflows/main.yml").read_text(encoding="utf-8")
    step = workflow.split(f"      - name: {name}\n", 1)[1].split("\n      - name:", 1)[0]
    script = step.split("        run: ", 1)[1]
    return textwrap.dedent(script[2:]) if script.startswith("|\n") else script.strip()


@pytest.fixture
def checker(tmp_path):
    shutil.copyfile(ROOT / "Makefile", tmp_path / "Makefile")
    (tmp_path / "datamimic_ce").mkdir()
    script = Path("script/architecture_study/archkeel_status.py")
    (tmp_path / script.parent).mkdir(parents=True)
    shutil.copyfile(ROOT / script, tmp_path / script)
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
            if "report" in args:
                if os.environ.get("REPORT_REFUSE") != "1":
                    output = Path(args[args.index("--output") + 1])
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_text(json.dumps({"producer_source": source}))
                sys.exit(int(os.environ.get("REPORT_EXIT", "0")))
            elif "validate" in args:
                print(os.environ["NATIVE_RECEIPT"], end="")
                sys.exit(int(os.environ["VALIDATION_EXIT"]))
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
        "MAKEFLAGS": f"ARCHKEEL_REVISION={ALTERNATE_REVISION}",
        "NATIVE_RECEIPT": receipt("UNKNOWN", 2),
        "VALIDATION_EXIT": "2",
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
    for name in ("Write report metadata", "Generate architecture report", "Capture native validation receipt"):
        result = subprocess.run(["bash", "-e", "-c", step_run(name)], cwd=directory, env=env, capture_output=True)
        assert result.returncode == 0, result.stderr
    output = directory / REPORT_DIR
    source = f"git+https://github.com/rapiddweller/archkeel@{ALTERNATE_REVISION}"
    assert json.loads((output / "metadata.json").read_text())["archkeel_revision"] == ALTERNATE_REVISION
    assert json.loads((output / "architecture.json").read_text())["producer_source"] == source
    assert (output / "validation.json").read_text() == env["NATIVE_RECEIPT"]
    gate = subprocess.run(["make", "architecture-check"], cwd=directory, env=env, capture_output=True)
    assert gate.returncode == 0, gate.stderr
    calls = [json.loads(line) for line in (directory / "calls.jsonl").read_text().splitlines()]
    checker_calls = [args for args in calls if "archkeel" in args]
    assert len(checker_calls) == 4
    assert all(args[args.index("--from") + 1] == source for args in checker_calls)
    assert all("--baseline" not in args for args in checker_calls)
    assert sum("validate" in args for args in checker_calls) == 2


@pytest.mark.parametrize(
    "native_receipt,exit_code,passes",
    [(receipt("PASS", 0), 0, True), (receipt("FAIL", 1), 1, False), ('{"outcome":"refusal"}', 2, False)],
)
def test_gate_uses_rules_and_rejects_a_refusal(checker, native_receipt, exit_code, passes):
    directory, env = checker
    env.update(NATIVE_RECEIPT=native_receipt, VALIDATION_EXIT=str(exit_code))
    result = subprocess.run(["make", "architecture-check"], cwd=directory, env=env, capture_output=True)
    assert (result.returncode == 0) is passes, result.stderr


@pytest.mark.parametrize("verdict,exit_code", [("FAIL", 1), ("UNKNOWN", 2)])
def test_nonpassing_verdict_preserves_reports_and_validation(checker, verdict, exit_code):
    directory, env = checker
    env.update(REPORT_EXIT=str(exit_code), VALIDATION_EXIT=str(exit_code), NATIVE_RECEIPT=receipt(verdict, exit_code))
    result = subprocess.run(
        ["make", "architecture-report", "architecture-validation-receipt"],
        cwd=directory,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    output = directory / REPORT_DIR
    assert (output / "architecture.json").exists()
    assert (output / "architecture.report.html").exists()
    assert (output / "validation.json").read_text() == env["NATIVE_RECEIPT"]


def test_refused_report_with_exit_two_cannot_pass_on_fresh_or_stale_files(checker):
    directory, env = checker
    env.update(REPORT_EXIT="2", REPORT_REFUSE="1")
    output = directory / REPORT_DIR
    output.mkdir(parents=True)
    stale = output / "architecture.json"
    stale.write_text('{"stale": true}')
    result = subprocess.run(
        ["make", "architecture-report"],
        cwd=directory,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert not stale.exists()
    assert not (output / "architecture.report.html").exists()
