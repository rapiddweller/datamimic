"""Append CI report data to the Pages tree; never execute artifact contents."""

import argparse
import html
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


def publish(archive: Path, site: Path, event: dict, prs: list[dict]) -> str:
    run = event["workflow_run"]
    repository = event["repository"]["full_name"]
    if (
        run["name"] != "Github Datamimic CE CI"
        or run["status"] != "completed"
        or run["head_repository"]["full_name"] != repository
    ):
        raise ValueError("Only completed same-repository CI reports can be published")
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
        "archkeel_version": "1.0.0",
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
    if run["event"] != "pull_request" and scanned != run["head_sha"]:
        raise ValueError("Push report scanned a different commit")
    if not isinstance(validation, dict) or validation.get("declared_rules") not in ("PASS", "FAIL", "UNKNOWN"):
        raise ValueError("Missing native architecture verdict")
    if any(
        not files[name].decode("utf-8").strip() for name in ("architecture.report.html", "architecture.detail.html")
    ):
        raise ValueError("Empty HTML report")
    relative = f"runs/{run['id']}/{run['run_attempt']}"
    destination = site / relative
    if destination.exists():
        if any((destination / name).read_bytes() != data for name, data in files.items()):
            raise ValueError("Immutable run report already exists with different content")
    else:
        destination.mkdir(parents=True)
        for name, data in files.items():
            (destination / name).write_bytes(data)
    scalars = (validation.get("measurements") or {}).get("scalars") or {}
    verdict = html.escape(str(validation["declared_rules"]))
    unknown = html.escape(str(scalars.get("unknown_positions", "not measured")))
    violations = html.escape(str(scalars.get("violations", "not measured")))
    receipt = (
        f"<h1>DATAMIMIC architecture review</h1><p>ArchKeel 1.0.0 · Run {run['id']}, attempt {run['run_attempt']}</p>"
        f"<p>Head: <code>{run['head_sha']}</code><br>Scanned: <code>{scanned}</code></p>"
        f"<p>Rules: {verdict} · Violations: {violations} · UNKNOWN positions: {unknown}</p>"
        "<p>Report publication is not architecture acceptance. Target completion remains subject to review.</p>"
        '<p><a href="architecture.report.html">Explore Actual / Target / Diff</a></p>'
        '<p><a href="architecture.json">Download JSON</a> · <a href="architecture.detail.html">Full detail</a>'
        ' · <a href="validation.json">Native validation receipt</a> · <a href="metadata.json">Provenance</a></p>'
        f'<p><a href="https://github.com/{html.escape(repository)}/actions/runs/{run["id"]}">Source CI run</a></p>'
    )
    (destination / "index.html").write_text(page(receipt), encoding="utf-8")
    if run["event"] == "pull_request":
        for pr in prs:
            if pr["head"]["sha"] == run["head_sha"]:
                number = pr["number"]
                if type(number) is not int or number < 1:
                    raise ValueError("Invalid PR identity")
                latest = site / "pr" / str(number)
                latest.mkdir(parents=True, exist_ok=True)
                previous_file = latest / "metadata.json"
                previous = json.loads(previous_file.read_text()) if previous_file.exists() else {}
                if previous.get("head_sha") == run["head_sha"] and (previous["run_id"], previous["run_attempt"]) > (
                    run["id"],
                    run["run_attempt"],
                ):
                    continue
                previous_file.write_bytes(files["metadata.json"])
                link = f"../../{relative}/"
                (latest / "index.html").write_text(
                    page(f'<meta http-equiv="refresh" content="0;url={link}"><a href="{link}">PR #{number} review</a>'),
                    encoding="utf-8",
                )
    # ponytail: one complete Pages tree; fail visibly at the hosting limit, never discard history.
    size = sum(path.stat().st_size for path in site.rglob("*") if path.is_file() and path.name != ".git")
    if size > 900 * 1024 * 1024:
        raise ValueError("Pages archive exceeds 900 MiB; report history was not deleted")
    links = sorted(
        site.glob("runs/*/*/metadata.json"), key=lambda path: tuple(map(int, path.parts[-3:-1])), reverse=True
    )
    (site / "index.html").write_text(
        page(
            "<h1>DATAMIMIC architecture reviews</h1>"
            "<p>Each run keeps its own HTML, JSON and validation evidence.</p><ul>"
            + "".join(
                f'<li><a href="{path.parent.relative_to(site)}/">Run {path.parts[-3]} / {path.parts[-2]}</a></li>'
                for path in links
            )
            + "</ul>"
        ),
        encoding="utf-8",
    )
    (site / ".nojekyll").touch()
    return relative + "/"


def page(body: str) -> str:
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>DATAMIMIC architecture review</title><body>'
        + body
        + "</body></html>"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--event", type=Path, required=True)
    parser.add_argument("--prs", type=Path, required=True)
    args = parser.parse_args()
    print(publish(args.archive, args.site, json.loads(args.event.read_text()), json.loads(args.prs.read_text())))
