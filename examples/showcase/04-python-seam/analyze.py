"""Plain-python postprocessing: the right tool for reporting over generated data.
Run after the engine: python analyze.py"""

import glob
import json
from collections import Counter


def exposure_by_bucket(rows: list[dict]) -> dict[str, int]:
    totals: Counter[str] = Counter()
    for row in rows:
        totals[row["risk_bucket"]] += row["limit_eur"]
    return dict(totals)


if __name__ == "__main__":
    files = glob.glob("output/**/cards.json", recursive=True)
    rows = [r for f in files for r in json.load(open(f))]
    assert rows, "run `datamimic run datamimic.xml` first"
    print(f"{len(rows)} cards | exposure by risk bucket: {exposure_by_bucket(rows)}")
