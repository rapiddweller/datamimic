"""Publish one development architecture snapshot; never execute artifact contents."""

import argparse
import json
import re
import stat
import zipfile
from pathlib import Path

FILES = {
    "architecture.json",
    "architecture.report.html",
    "architecture.detail.html",
    "validation.json",
    "metadata.json",
}


def configured_archkeel_version() -> str:
    makefile = Path(__file__).resolve().parents[2] / "Makefile"
    pin = re.search(r"^ARCHKEEL_SOURCE := archkeel==(\S+)$", makefile.read_text(), re.MULTILINE)
    if pin is None:
        raise ValueError("Makefile must pin the approved ArchKeel version")
    return pin[1]


def publish(archive: Path, site: Path, event: dict) -> None:
    run = event["workflow_run"]
    repository = event["repository"]["full_name"]
    if (
        run.get("path") != ".github/workflows/main.yml"
        or run["status"] != "completed"
        or run["head_repository"]["full_name"] != repository
        or run.get("head_branch") != "development"
        or run["event"] not in ("push", "workflow_dispatch")
    ):
        raise ValueError("Only completed development CI reports from this repository can be published")
    for field in ("id", "run_attempt"):
        if type(run[field]) is not int or run[field] < 1:
            raise ValueError("Invalid run identity")
    if not re.fullmatch(r"[0-9a-f]{40}", run["head_sha"]):
        raise ValueError("Invalid head SHA")
    with zipfile.ZipFile(archive) as zipped:
        members = zipped.infolist()
        if len(members) != len(FILES) or {m.filename for m in members} != FILES:
            raise ValueError("Artifact must contain exactly the five report files")
        if any(stat.S_IFMT(m.external_attr >> 16) not in (0, stat.S_IFREG) for m in members):
            raise ValueError("Artifact links and special files are not allowed")
        if sum(m.file_size for m in members) > 200 * 1024 * 1024:
            raise ValueError("Report artifact exceeds 200 MiB")
        files = {m.filename: zipped.read(m) for m in members}
    metadata = json.loads(files["metadata.json"])
    expected = {
        "repository": repository,
        "run_id": run["id"],
        "run_attempt": run["run_attempt"],
        "head_sha": run["head_sha"],
        "archkeel_version": configured_archkeel_version(),
    }
    if any(metadata.get(key) != value for key, value in expected.items()):
        raise ValueError("Report identity does not match the triggering CI run")
    scanned = metadata.get("scanned_sha", "")
    if not isinstance(scanned, str) or not re.fullmatch(r"[0-9a-f]{40}", scanned):
        raise ValueError("Missing scanned commit")
    report = json.loads(files["architecture.json"])
    validation = json.loads(files["validation.json"])
    if not isinstance(report, dict) or report.get("source", {}).get("git_head") != scanned:
        raise ValueError("Report and metadata identify different scans")
    if scanned != run["head_sha"]:
        raise ValueError("Development report scanned a different commit")
    if not isinstance(validation, dict) or validation.get("declared_rules") not in ("PASS", "FAIL", "UNKNOWN"):
        raise ValueError("Missing native architecture verdict")
    if any(
        not files[name].decode("utf-8").strip() for name in ("architecture.report.html", "architecture.detail.html")
    ):
        raise ValueError("Empty HTML report")
    if site.exists() and any(site.iterdir()):
        raise ValueError("Publish into an empty site; historical reports must not be included")
    site.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (site / name).write_bytes(data)
    (site / "index.html").write_bytes(files["architecture.report.html"])
    (site / ".nojekyll").touch()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--event", type=Path, required=True)
    args = parser.parse_args()
    publish(args.archive, args.site, json.loads(args.event.read_text()))
    print("Published the current development architecture at index.html")
