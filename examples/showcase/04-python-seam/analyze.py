"""Plain-python postprocessing: the right tool for reporting over generated data.
Run after the engine: python analyze.py"""

import json
from collections import Counter
from pathlib import Path


def exposure_by_bucket(rows: list[dict]) -> dict[str, int]:
    totals: Counter[str] = Counter()
    for row in rows:
        totals[row["risk_bucket"]] += row["limit_eur"]
    return dict(totals)


if __name__ == "__main__":
    # script-relative, so the command works from any working directory
    files = sorted((Path(__file__).parent / "output").rglob("cards.json"))
    rows = [r for f in files for r in json.loads(f.read_text())]
    assert rows, "run `datamimic run examples/showcase/04-python-seam/datamimic.xml` first"
    print(f"{len(rows)} cards | exposure by risk bucket: {exposure_by_bucket(rows)}")
