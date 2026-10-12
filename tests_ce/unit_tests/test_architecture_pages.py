"""Publish reports without losing red results, provenance, or older reviews."""

import hashlib
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
    ],
)
def test_download_step_handles_paginated_metadata_and_missing_artifacts(
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
  */artifacts) printf '%s' "$REPORT_ARTIFACT" ;;
  */jobs) printf '[{"jobs":[{"name":"Other"}]},{"jobs":[{"name":"%s"}]}]' "$REPORT_JOB" ;;
  */artifacts/*/zip) printf 'report archive' ;;
  */commits/*/pulls)
    [[ "$REPORT_JOB" != 'API failure' ]] || exit 9
    printf '[[{"number":7}],[{"number":8}]]' ;;
  */pulls\\?*) printf '[[{"number":9}],[{"number":10}]]' ;;
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
            "SOURCE_SHA": SHA,
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
    if artifact and expected_status == 0:
        assert json.loads((tmp_path / "prs.json").read_text()) == [{"number": 7}, {"number": 8}]
        assert json.loads((tmp_path / "open-prs.json").read_text()) == [9, 10]


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
            "event": "pull_request",
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
        "archkeel_version": "2.0.0",
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


def tree_digests(path):
    return {
        item.relative_to(path).as_posix(): hashlib.sha256(item.read_bytes()).hexdigest()
        for item in path.rglob("*")
        if item.is_file()
    }


def test_red_report_is_downloadable_and_history_survives_stale_run(tmp_path):
    module = publisher()
    site = tmp_path / "site"
    first = event()
    module.publish(archive(tmp_path / "first.zip", first), site, first, [{"number": 274, "head": {"sha": SHA}}])
    receipt = site / "runs/10/1/validation.json"
    assert json.loads(receipt.read_text())["observation_complete"] == "UNKNOWN"
    assert "FAIL" in (site / "runs/10/1/index.html").read_text()
    assert "202" in (site / "runs/10/1/index.html").read_text()
    assert f"ArchKeel {module.configured_archkeel_version()}" in (site / "runs/10/1/index.html").read_text()
    saved = receipt.read_bytes()
    next_sha = "b" * 40
    newer = event(11, sha=next_sha)
    module.publish(archive(tmp_path / "next.zip", newer), site, newer, [{"number": 274, "head": {"sha": next_sha}}])
    latest = (site / "pr/274/index.html").read_text()
    assert "../../runs/11/1/" in latest
    module.publish(archive(tmp_path / "retry.zip", first), site, first, [{"number": 274, "head": {"sha": next_sha}}])
    assert (site / "pr/274/index.html").read_text() == latest
    assert receipt.read_bytes() == saved
    retry = event(11, 2, next_sha)
    module.publish(archive(tmp_path / "attempt.zip", retry), site, retry, [])
    assert (site / "runs/11/1/index.html").is_file()
    assert (site / "runs/11/2/index.html").is_file()


@pytest.mark.parametrize(
    "changes", [{"run_id": 99}, {"head_sha": "b" * 40}, {"archkeel_version": "0.8.5"}, {"archkeel_version": "1.0.0"}]
)
def test_mismatched_identity_cannot_publish(tmp_path, changes):
    source = event()
    with pytest.raises(ValueError):
        publisher().publish(archive(tmp_path / "bad.zip", source, **changes), tmp_path / "site", source, [])
    assert not (tmp_path / "site/runs").exists()


@pytest.mark.parametrize(
    "changes",
    [
        {"path": ".github/workflows/other.yml"},
        {"path": None},
        {"status": "in_progress"},
        {"head_repository": {"full_name": "other/repository"}},
    ],
)
def test_untrusted_or_incomplete_workflow_cannot_publish(tmp_path, changes):
    source = event()
    source["workflow_run"].update(changes)
    with pytest.raises(ValueError, match="Only completed same-repository CI reports"):
        publisher().publish(archive(tmp_path / "untrusted.zip", source), tmp_path / "site", source, [])
    assert not (tmp_path / "site/runs").exists()


@pytest.mark.parametrize("name,mode", [("../outside", 0), ("/absolute", 0), ("setup.py", 0), ("link", stat.S_IFLNK)])
def test_archive_cannot_write_or_execute_unexpected_files(tmp_path, name, mode):
    source = event()
    path = archive(tmp_path / "attack.zip", source)
    with zipfile.ZipFile(path, "a") as zipped:
        member = zipfile.ZipInfo(name)
        member.external_attr = mode << 16
        zipped.writestr(member, "sentinel")
    with pytest.raises(ValueError):
        publisher().publish(path, tmp_path / "site", source, [])
    assert not (tmp_path / "outside").exists()
    assert not (tmp_path / "site/runs").exists()


def test_incomplete_report_cannot_replace_an_existing_review(tmp_path):
    source = event()
    path = tmp_path / "incomplete.zip"
    with zipfile.ZipFile(path, "w") as zipped:
        zipped.writestr("architecture.json", "{}")
    with pytest.raises(ValueError):
        publisher().publish(path, tmp_path / "site", source, [])
    assert not (tmp_path / "site/runs").exists()


@pytest.mark.parametrize("name", ["metadata.json", "architecture.json", "validation.json"])
def test_malformed_json_cannot_publish(tmp_path, name):
    source = event()
    path = archive(tmp_path / "bad-json.zip", source)
    replace_member(path, name, b"{truncated")

    with pytest.raises(ValueError):
        publisher().publish(path, tmp_path / "site", source, [])
    assert not (tmp_path / "site/runs").exists()


def test_non_utf8_html_cannot_publish(tmp_path):
    source = event()
    path = archive(tmp_path / "bad-html.zip", source)
    replace_member(path, "architecture.report.html", b"\xff\xfe")

    with pytest.raises(ValueError):
        publisher().publish(path, tmp_path / "site", source, [])
    assert not (tmp_path / "site/runs").exists()


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
        publisher().publish(path, tmp_path / "site", source, [])
    assert not (tmp_path / "site/runs").exists()


def test_duplicate_archive_member_cannot_publish(tmp_path):
    source = event()
    path = archive(tmp_path / "duplicate.zip", source)
    with zipfile.ZipFile(path, "a") as zipped, pytest.warns(UserWarning, match="Duplicate name"):
        zipped.writestr("architecture.json", json.dumps({"source": {"git_head": SHA}}))

    with pytest.raises(ValueError):
        publisher().publish(path, tmp_path / "site", source, [])
    assert not (tmp_path / "site/runs").exists()


def test_allowlisted_report_symlink_cannot_publish(tmp_path):
    source = event()
    path = archive(tmp_path / "symlink.zip", source)
    report = json.dumps({"source": {"git_head": SHA}}).encode()
    replace_member(path, "architecture.json", report, stat.S_IFLNK | 0o777)

    with pytest.raises(ValueError):
        publisher().publish(path, tmp_path / "site", source, [])
    assert not (tmp_path / "site/runs").exists()


def test_identical_run_attempt_is_idempotent(tmp_path):
    source = event()
    path = archive(tmp_path / "same.zip", source)
    site = tmp_path / "site"
    module = publisher()
    assert module.publish(path, site, source, [{"number": 274, "head": {"sha": SHA}}]) == "runs/10/1/"
    before = tree_bytes(site)

    assert module.publish(path, site, source, [{"number": 274, "head": {"sha": SHA}}]) == "runs/10/1/"
    assert tree_bytes(site) == before


def test_different_content_for_same_run_attempt_preserves_first_publication(tmp_path):
    source = event()
    original = archive(tmp_path / "original.zip", source)
    changed = archive(tmp_path / "changed.zip", source)
    with zipfile.ZipFile(changed) as zipped:
        receipt = json.loads(zipped.read("validation.json"))
    receipt["measurements"]["scalars"]["violations"] = 92
    replace_member(changed, "validation.json", json.dumps(receipt).encode())

    site = tmp_path / "site"
    module = publisher()
    prs = [{"number": 274, "head": {"sha": SHA}}]
    module.publish(original, site, source, prs)
    before = tree_bytes(site)
    with pytest.raises(ValueError):
        module.publish(changed, site, source, prs)
    assert tree_bytes(site) == before


def test_older_attempt_does_not_replace_pr_latest(tmp_path):
    module = publisher()
    site = tmp_path / "site"
    prs = [{"number": 274, "head": {"sha": SHA}}]
    second = event(10, 2)
    first = event(10, 1)
    module.publish(archive(tmp_path / "attempt-2.zip", second), site, second, prs)
    latest_before = (site / "pr/274/index.html").read_bytes()

    module.publish(archive(tmp_path / "attempt-1.zip", first), site, first, prs)

    assert (site / "pr/274/index.html").read_bytes() == latest_before
    assert "runs/10/2/" in latest_before.decode()
    assert (site / "runs/10/1/index.html").exists()


def test_pages_keeps_current_details_and_archived_reviews_without_changing_evidence(tmp_path):
    module = publisher()
    site = tmp_path / "archive"
    first = event()
    path = archive(tmp_path / "old.zip", first)
    projection = {
        "atlas": {"architecture_href": "architecture.json", "detail_page": "architecture.detail.html"},
        "components": [{"id": "runtime", "responsibility": "Execute statements."}],
    }
    report = '<html><body><script id="flow-data" type="application/json">' + json.dumps(projection) + "</script></body>"
    replace_member(path, "architecture.report.html", report.encode())
    module.publish(path, site, first, [])
    second = event(11, sha="b" * 40)
    module.publish(
        archive(tmp_path / "current.zip", second), site, second, [{"number": 274, "head": {"sha": "b" * 40}}]
    )
    original = tree_bytes(site)
    output = tmp_path / "pages"

    module.project_pages(site, output, "runs/11/1/", [274])

    assert tree_bytes(site) == original
    assert (output / "runs/11/1/architecture.detail.html").read_bytes() == original[
        "runs/11/1/architecture.detail.html"
    ]
    historical = (output / "runs/10/1/architecture.report.html").read_text()
    assert "Historical review" in historical
    assert "Execute statements." in historical
    assert (
        "https://raw.githubusercontent.com/rapiddweller/datamimic/architecture-reports/runs/10/1/architecture.json"
        in historical
    )
    assert not (output / "runs/10/1/architecture.json").exists()
    landing = (output / "runs/10/1/architecture.detail.html").read_text()
    assert "Download" in landing
    assert "raw.githubusercontent.com" in landing


def test_open_pr_latest_keeps_full_detail_when_another_run_is_current(tmp_path):
    module = publisher()
    site = tmp_path / "archive"
    first = event()
    module.publish(archive(tmp_path / "pr.zip", first), site, first, [{"number": 274, "head": {"sha": SHA}}])
    second = event(11, sha="b" * 40)
    module.publish(archive(tmp_path / "other.zip", second), site, second, [])
    output = tmp_path / "pages"

    module.project_pages(site, output, "runs/11/1/", [274])

    assert (output / "runs/10/1/architecture.json").read_bytes() == (site / "runs/10/1/architecture.json").read_bytes()
    assert (output / "runs/10/1/architecture.detail.html").read_bytes() == (
        site / "runs/10/1/architecture.detail.html"
    ).read_bytes()


def test_pages_projection_preserves_flow_data_and_archive_evidence(tmp_path):
    module = publisher()
    site = tmp_path / "archive"
    current = site / "runs/11/1"
    historical = site / "runs/10/1"
    current.mkdir(parents=True)
    historical.mkdir(parents=True)
    historical_data = {
        "atlas": {
            "architecture_href": "architecture.json",
            "detail_page": "architecture.detail.html",
            "components": [{"id": "runtime", "responsibility": "Execute statements."}],
            "qa_escape_probe": "<img src=x onerror=alert(1)>",
        },
        "navigation": {"main_href": "index.html"},
    }
    report = (
        '<!doctype html><html><body><a href="architecture.json">JSON</a>'
        '<script id="flow-data" type="application/json">' + json.dumps(historical_data) + "</script></body></html>"
    )
    old_files = {
        "architecture.report.html": report,
        "architecture.json": '{"historical":true}',
        "architecture.detail.html": "original historical details",
        "validation.json": '{"declared_rules":"FAIL"}',
        "metadata.json": '{"run_id":10,"run_attempt":1}',
    }
    current_files = {
        "architecture.report.html": "<!doctype html><html><body>current report</body></html>",
        "architecture.json": '{"current":true}',
        "architecture.detail.html": "current full details",
        "validation.json": '{"declared_rules":"UNKNOWN"}',
        "metadata.json": '{"run_id":11,"run_attempt":1}',
    }
    for name, content in old_files.items():
        (historical / name).write_text(content, encoding="utf-8")
    for name, content in current_files.items():
        (current / name).write_text(content, encoding="utf-8")
    for run in (historical, current):
        (run / "index.html").write_text('<a href="architecture.json">JSON</a>', encoding="utf-8")
    latest = site / "pr/274"
    latest.mkdir(parents=True)
    (latest / "metadata.json").write_text('{"run_id":11,"run_attempt":1}', encoding="utf-8")

    archived_before = tree_digests(site)
    output = tmp_path / "pages"

    module.project_pages(site, output, "runs/11/1/", [274])

    assert tree_digests(site) == archived_before
    for name, content in current_files.items():
        assert (output / "runs/11/1" / name).read_bytes() == content.encode("utf-8")
    historical_page = (output / "runs/10/1/architecture.report.html").read_text(encoding="utf-8")
    projected = re.search(r'(<script\b[^>]*\bid="flow-data"[^>]*>)(.*?)(</script>)', historical_page, re.DOTALL)
    assert projected is not None
    assert "<" not in projected[2]
    projected_data = json.loads(projected[2])
    expected_data = json.loads(json.dumps(historical_data))
    expected_data["atlas"]["architecture_href"] = (
        "https://raw.githubusercontent.com/rapiddweller/datamimic/architecture-reports/runs/10/1/architecture.json"
    )
    assert projected_data == expected_data
    assert "\\u003cimg" in projected[2]
    assert "Historical review" in historical_page
    assert not (output / "runs/10/1/architecture.json").exists()
    detail_landing = (output / "runs/10/1/architecture.detail.html").read_text(encoding="utf-8")
    assert "Download original full-detail HTML" in detail_landing
    assert "runs/10/1/architecture.detail.html" in detail_landing
