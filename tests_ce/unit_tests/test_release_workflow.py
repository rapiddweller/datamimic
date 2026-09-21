"""Release workflow artifact selection contract."""

import re
from pathlib import Path


def test_release_downloads_only_the_package_artifact() -> None:
    workflow = (Path(__file__).resolve().parents[2] / ".github/workflows/main.yml").read_text(encoding="utf-8")
    release = workflow.split("\n  release:\n", maxsplit=1)[1]
    steps = re.findall(r"(?ms)^      - .*?(?=^      - |\Z)", release)
    download_steps = [step for step in steps if "uses: actions/download-artifact@" in step]
    assert len(download_steps) == 1
    download = download_steps[0]

    assert re.search(r"(?m)^          name: artifact$", download)
    assert re.search(r"(?m)^          path: dist$", download)
