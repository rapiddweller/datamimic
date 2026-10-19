"""Publish reports without losing red results, provenance, or older reviews."""

import importlib.util
import json
import os
import re
import stat
import subprocess
import textwrap
import zipfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "script/architecture_study/publish_reports.py"
SHA = "a" * 40


@pytest.mark.parametrize(
    "artifact,job,expected_status,available",
    [
        ("42", "Architecture review report", 0, "true"),
        ("", "Unit tests", 0, "false"),
        ("", "Architecture review report", 1, None),
        ("42", "API failure", 9, None),
        ("42", "Older run", 0, "false"),
        ("42", "Older attempt", 0, "false"),
        ("42", "Invalid latest", 1, None),
        ("42", "Manual latest", 0, "true"),
    ],
)
def test_download_step_only_accepts_latest_run_and_handles_missing_artifacts(
    tmp_path, artifact, job, expected_status, available
):
    workflow = SCRIPT.parents[2] / ".github/workflows/architecture-pages.yml"
    download = re.search(
        r"- name: Download this attempt's report data.*?run: \|\n(.*?)\n      - name:",
        workflow.read_text(),
        re.DOTALL,
    )
    assert download is not None
    gh = tmp_path / "gh"
    gh.write_text("""#!/bin/bash
if [[ "$*" == *--slurp* && "$*" == *--jq* ]]; then
  echo 'the --slurp option is not supported with --jq' >&2
  exit 1
fi
case "$2" in
  */workflows/main.yml/runs\\?*)
    [[ "$REPORT_JOB" != 'API failure' ]] || exit 9
    case "$REPORT_JOB" in
      'Older run') printf '2/1' ;;
      'Older attempt') printf '1/2' ;;
      'Invalid latest') printf 'null/null' ;;
      'Manual latest') printf '2/3' ;;
      *) printf '1/1' ;;
    esac ;;
  */artifacts) printf '%s' "$REPORT_ARTIFACT" ;;
  */jobs) printf '[{"jobs":[{"name":"Other"}]},{"jobs":[{"name":"%s"}]}]' "$REPORT_JOB" ;;
  */artifacts/*/zip) printf 'report archive' ;;
  */actions/runs/[0-9]*) printf '{"id":%s}' "${2##*/}" ;;
  *) exit 2 ;;
esac
""")
    gh.chmod(0o755)
    result = subprocess.run(
        ["bash", "-e", "-c", textwrap.dedent(download[1])],
        env={
            **os.environ,
            "PATH": f"{tmp_path}:{os.environ['PATH']}",
            "REPORT_ARTIFACT": artifact,
            "REPORT_JOB": job,
            "REPOSITORY": "owner/repo",
            "SOURCE_RUN": "1",
            "SOURCE_ATTEMPT": "1",
            "GITHUB_EVENT_NAME": "workflow_dispatch" if job == "Manual latest" else "workflow_run",
            "RUNNER_TEMP": str(tmp_path),
            "GITHUB_OUTPUT": str(tmp_path / "output"),
            "GITHUB_STEP_SUMMARY": str(tmp_path / "summary"),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == expected_status, result.stderr
    if available is not None:
        assert (tmp_path / "output").read_text() == f"available={available}\n"
    else:
        assert not (tmp_path / "output").exists()
        if not artifact:
            assert "artifact is absent or expired" in result.stderr
        if job == "Invalid latest":
            assert "Cannot identify the latest development run" in result.stderr
    if available == "true":
        assert (tmp_path / "report.zip").read_text() == "report archive"
        source = json.loads((tmp_path / "source-event.json").read_text())
        assert source["repository"]["full_name"] == "owner/repo"
        assert source["workflow_run"]["id"] == (2 if job == "Manual latest" else 1)
    else:
        assert not (tmp_path / "report.zip").exists()


def publisher():
    spec = importlib.util.spec_from_file_location("publish_reports", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def event(run=10, attempt=1, sha=SHA):
    return {
        "repository": {"full_name": "rapiddweller/datamimic"},
        "workflow_run": {
            "id": run,
            "run_attempt": attempt,
            "head_sha": sha,
            "head_repository": {"full_name": "rapiddweller/datamimic"},
            "name": "ake2l is running Github Datamimic CE CI on rapiddweller/datamimic",
            "path": ".github/workflows/main.yml",
            "status": "completed",
            "event": "push",
            "head_branch": "development",
        },
    }


def archive(path, source, **changes):
    run = source["workflow_run"]
    metadata = {
        "repository": "rapiddweller/datamimic",
        "run_id": run["id"],
        "run_attempt": run["run_attempt"],
        "head_sha": run["head_sha"],
        "scanned_sha": run["head_sha"],
        "archkeel_version": "4.0.1",
    }
    metadata.update(changes)
    files = {
        "metadata.json": json.dumps(metadata),
        "architecture.json": json.dumps({"source": {"git_head": metadata["scanned_sha"]}}),
        "architecture.report.html": "<!doctype html><title>Actual, Target, Diff</title>",
        "architecture.detail.html": "<!doctype html><title>Detail</title>",
        "validation.json": json.dumps(
            {
                "declared_rules": "FAIL",
                "observation_complete": "UNKNOWN",
                "measurements": {"scalars": {"violations": 91, "unknown_positions": 202}},
            }
        ),
    }
    with zipfile.ZipFile(path, "w") as zipped:
        for name, content in files.items():
            zipped.writestr(name, content)
    return path


def replace_member(path, name, content, mode=None):
    with zipfile.ZipFile(path) as zipped:
        entries = [(member.filename, zipped.read(member), member.external_attr) for member in zipped.infolist()]
    with zipfile.ZipFile(path, "w") as zipped:
        for existing_name, existing_content, external_attr in entries:
            if existing_name == name:
                info = zipfile.ZipInfo(existing_name)
                info.external_attr = (mode << 16) if mode is not None else external_attr
                zipped.writestr(info, content)
            else:
                zipped.writestr(existing_name, existing_content)


def tree_bytes(path):
    return {item.relative_to(path).as_posix(): item.read_bytes() for item in path.rglob("*") if item.is_file()}


def test_only_current_snapshot_is_published_with_native_explorer_and_unchanged_evidence(tmp_path):
    module = publisher()
    source = event()
    path = archive(tmp_path / "report.zip", source)
    site = tmp_path / "site"

    module.publish(path, site, source)

    assert {item.name for item in site.iterdir()} == module.FILES | {"index.html", ".nojekyll"}
    with zipfile.ZipFile(path) as zipped:
        for name in module.FILES:
            assert (site / name).read_bytes() == zipped.read(name)
    assert (site / "index.html").read_bytes() == (site / "architecture.report.html").read_bytes()
    assert json.loads((site / "validation.json").read_text())["declared_rules"] == "FAIL"
    assert not (site / "runs").exists()
    assert not (site / "pr").exists()


@pytest.mark.parametrize(
    "changes",
    [
        {"run_id": 99},
        {"head_sha": "b" * 40},
        {"archkeel_version": "0.8.5"},
        {"archkeel_version": "1.0.0"},
        {"archkeel_version": "2.0.0"},
        {"archkeel_version": "3.0.1"},
    ],
)
def test_mismatched_identity_cannot_publish(tmp_path, changes):
    source = event()
    with pytest.raises(ValueError):
        publisher().publish(archive(tmp_path / "bad.zip", source, **changes), tmp_path / "site", source)
    assert not (tmp_path / "site").exists()


@pytest.mark.parametrize(
    "changes",
    [
        {"path": ".github/workflows/other.yml"},
        {"path": None},
        {"status": "in_progress"},
        {"head_branch": "feature"},
        {"event": "pull_request"},
        {"head_repository": {"full_name": "other/repository"}},
    ],
)
def test_untrusted_or_incomplete_workflow_cannot_publish(tmp_path, changes):
    source = event()
    source["workflow_run"].update(changes)
    with pytest.raises(ValueError, match="Only completed development CI reports"):
        publisher().publish(archive(tmp_path / "untrusted.zip", source), tmp_path / "site", source)
    assert not (tmp_path / "site").exists()


@pytest.mark.parametrize("name,mode", [("../outside", 0), ("/absolute", 0), ("setup.py", 0), ("link", stat.S_IFLNK)])
def test_archive_cannot_write_or_execute_unexpected_files(tmp_path, name, mode):
    source = event()
    path = archive(tmp_path / "attack.zip", source)
    with zipfile.ZipFile(path, "a") as zipped:
        member = zipfile.ZipInfo(name)
        member.external_attr = mode << 16
        zipped.writestr(member, "sentinel")
    with pytest.raises(ValueError):
        publisher().publish(path, tmp_path / "site", source)
    assert not (tmp_path / "outside").exists()
    assert not (tmp_path / "site").exists()


def test_incomplete_report_cannot_replace_an_existing_review(tmp_path):
    source = event()
    path = tmp_path / "incomplete.zip"
    with zipfile.ZipFile(path, "w") as zipped:
        zipped.writestr("architecture.json", "{}")
    with pytest.raises(ValueError):
        publisher().publish(path, tmp_path / "site", source)
    assert not (tmp_path / "site").exists()


@pytest.mark.parametrize("name", ["metadata.json", "architecture.json", "validation.json"])
def test_malformed_json_cannot_publish(tmp_path, name):
    source = event()
    path = archive(tmp_path / "bad-json.zip", source)
    replace_member(path, name, b"{truncated")

    with pytest.raises(ValueError):
        publisher().publish(path, tmp_path / "site", source)
    assert not (tmp_path / "site").exists()


def test_non_utf8_html_cannot_publish(tmp_path):
    source = event()
    path = archive(tmp_path / "bad-html.zip", source)
    replace_member(path, "architecture.report.html", b"\xff\xfe")

    with pytest.raises(ValueError):
        publisher().publish(path, tmp_path / "site", source)
    assert not (tmp_path / "site").exists()


@pytest.mark.parametrize("field", ["report_sha", "push_scan_sha"])
def test_report_scan_identity_must_match_metadata_and_push_head(tmp_path, field):
    source = event()
    path = archive(tmp_path / "mixed-scan.zip", source)
    if field == "report_sha":
        with zipfile.ZipFile(path) as zipped:
            report = json.loads(zipped.read("architecture.json"))
        report["source"]["git_head"] = "b" * 40
        replace_member(path, "architecture.json", json.dumps(report).encode())
    else:
        # Push reports must describe the triggering commit. PR reports may
        # legitimately scan a merge ref, so this check uses a push event.
        source = event()
        source["workflow_run"]["event"] = "push"
        path = archive(tmp_path / "mixed-scan.zip", source, scanned_sha="b" * 40)

    with pytest.raises(ValueError):
        publisher().publish(path, tmp_path / "site", source)
    assert not (tmp_path / "site").exists()


def test_duplicate_archive_member_cannot_publish(tmp_path):
    source = event()
    path = archive(tmp_path / "duplicate.zip", source)
    with zipfile.ZipFile(path, "a") as zipped, pytest.warns(UserWarning, match="Duplicate name"):
        zipped.writestr("architecture.json", json.dumps({"source": {"git_head": SHA}}))

    with pytest.raises(ValueError):
        publisher().publish(path, tmp_path / "site", source)
    assert not (tmp_path / "site").exists()


def test_allowlisted_report_symlink_cannot_publish(tmp_path):
    source = event()
    path = archive(tmp_path / "symlink.zip", source)
    report = json.dumps({"source": {"git_head": SHA}}).encode()
    replace_member(path, "architecture.json", report, stat.S_IFLNK | 0o777)

    with pytest.raises(ValueError):
        publisher().publish(path, tmp_path / "site", source)
    assert not (tmp_path / "site").exists()


def test_nonempty_destination_is_rejected_without_changing_its_current_snapshot(tmp_path):
    module = publisher()
    site = tmp_path / "site"
    first = event()
    module.publish(archive(tmp_path / "first.zip", first), site, first)
    before = tree_bytes(site)
    newer = event(run=11)

    with pytest.raises(ValueError, match="empty site"):
        module.publish(archive(tmp_path / "new.zip", newer), site, newer)

    assert tree_bytes(site) == before
