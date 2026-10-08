"""Publish reports without losing red results, provenance, or older reviews."""

import importlib.util
import json
import stat
import zipfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "script/architecture_study/publish_reports.py"
SHA = "a" * 40


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
            "name": "Github Datamimic CE CI",
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
        "archkeel_version": "1.0.0",
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


def test_red_report_is_downloadable_and_history_survives_stale_run(tmp_path):
    module = publisher()
    site = tmp_path / "site"
    first = event()
    module.publish(archive(tmp_path / "first.zip", first), site, first, [{"number": 274, "head": {"sha": SHA}}])
    receipt = site / "runs/10/1/validation.json"
    assert json.loads(receipt.read_text())["observation_complete"] == "UNKNOWN"
    assert "FAIL" in (site / "runs/10/1/index.html").read_text()
    assert "202" in (site / "runs/10/1/index.html").read_text()
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


@pytest.mark.parametrize("changes", [{"run_id": 99}, {"head_sha": "b" * 40}, {"archkeel_version": "0.8.5"}])
def test_mismatched_identity_cannot_publish(tmp_path, changes):
    source = event()
    with pytest.raises(ValueError):
        publisher().publish(archive(tmp_path / "bad.zip", source, **changes), tmp_path / "site", source, [])
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
