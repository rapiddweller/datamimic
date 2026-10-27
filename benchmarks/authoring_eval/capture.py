# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Run one project and print the rows it produced as JSON (#412).

    python -m benchmarks.authoring_eval.capture <project-dir>

The oracle starts this in a fresh interpreter for each run, because a second run in the same process hides state
that lives in the process, such as the hash order of strings."""

import contextlib
import json
import sys
from pathlib import Path

from pydantic import BaseModel

from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH
from datamimic_ce.engine.dsl.api import NAME_SEPARATOR
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


class Capture(BaseModel):
    error: str | None = None  # exception class name when the run failed
    rows: dict[str, list[dict[str, object]]] = {}


def run(project: Path) -> Capture:
    try:
        engine = DataMimicTest(test_dir=project, filename=PROJECT_ENTRY_PATH, capture_test_result=True)
        engine.test_with_timer()
    except Exception as error:  # an untrusted project can fail in any way; the class name is the whole reason
        return Capture(error=type(error).__name__)
    captured = engine.capture_result() or {}
    # The engine names a product nested two levels deep "inner|leaf"; Build and the checks name it "leaf".
    return Capture(
        rows={product.rsplit(NAME_SEPARATOR, 1)[-1]: [dict(row) for row in rows] for product, rows in captured.items()}
    )


def main(argv: list[str]) -> int:
    with contextlib.redirect_stdout(sys.stderr):  # the engine logs to stdout; keep stdout one JSON document
        capture = run(Path(argv[0]))
    # default=str: a subject row can hold any type; JSON keeps int, float, bool and str apart, which the checks need
    print(json.dumps(capture.model_dump(), default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
