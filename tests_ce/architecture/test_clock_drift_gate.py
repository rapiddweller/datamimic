"""Wall-clock drift gate.

AST-walks the CE production tree and fails if any production module
reads the wall-clock through anything other than the sanctioned SPOT
in ``datamimic_ce.domains.domain_core.runtime.clock``.

Forbidden patterns (anywhere in ``datamimic_ce/**`` except the
allow-list below):

* ``datetime.now(...)`` and ``datetime.utcnow(...)``
* ``datetime.today(...)``
* ``time.time()``

The allow-list captures intentional exceptions:

* ``clock.py`` — the SPOT itself.
* ``datetime_generator.py`` — has a documented "current datetime" mode
  where the *output* is meant to be the live wall-clock.
* ``utils/logging_util.py`` and ``data_mimic_test.py`` — telemetry
  timestamps; not part of generator output.

Adding a new wall-clock callsite means either (a) routing it through
``now_utc_naive()`` / ``resolve_clock(...)``, or (b) adding the file
to the allow-list with a comment explaining why.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PROD_ROOT = Path(__file__).resolve().parents[2] / "datamimic_ce"

# Files allowed to read the wall-clock directly. Keep this list small;
# every entry is a discipline exception that future reviewers should
# verify still applies.
ALLOWLIST: set[str] = {
    # SPOT itself: now_utc_naive() lives here.
    "datamimic_ce/domains/domain_core/runtime/clock.py",
    # Intentional "current datetime" output mode in datetime_generator.
    "datamimic_ce/domains/common/literal_generators/datetime_generator.py",
    # Telemetry / timing, not part of generator output.
    "datamimic_ce/utils/logging_util.py",
    "datamimic_ce/data_mimic_test.py",
}

# Method names on datetime / time module that read the wall-clock.
FORBIDDEN_DATETIME_METHODS = {"now", "utcnow", "today"}
FORBIDDEN_TIME_FUNCS = {"time"}


def _collect_callsites(tree: ast.AST) -> list[tuple[int, str]]:
    """Return ``(lineno, expr)`` for each forbidden wall-clock callsite."""
    hits: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        # datetime.now() / datetime.utcnow() / datetime.today()
        if isinstance(func, ast.Attribute) and func.attr in FORBIDDEN_DATETIME_METHODS:
            # The receiver must look like the datetime class. We accept any
            # form whose attribute chain ends in `.datetime` or that is a
            # bare `datetime` Name — covers `datetime.now()`,
            # `dt.datetime.now()`, and `from datetime import datetime`.
            receiver = func.value
            if _looks_like_datetime(receiver):
                hits.append((node.lineno, f"datetime.{func.attr}(...)"))
        # time.time()
        elif (
            isinstance(func, ast.Attribute)
            and func.attr in FORBIDDEN_TIME_FUNCS
            and isinstance(func.value, ast.Name)
            and func.value.id == "time"
        ):
            hits.append((node.lineno, "time.time()"))
    return hits


def _looks_like_datetime(node: ast.AST) -> bool:
    """Recognise a `datetime` reference: bare Name or Attribute chain
    ending in ``datetime``."""
    if isinstance(node, ast.Name) and node.id == "datetime":
        return True
    if isinstance(node, ast.Attribute) and node.attr == "datetime":
        return True
    return False


def _production_modules() -> list[Path]:
    """Return every .py file under datamimic_ce/, sorted, excluding
    demos and any test/__pycache__ paths."""
    skip_segments = {"demos", "__pycache__"}
    return sorted(p for p in PROD_ROOT.rglob("*.py") if not any(seg in p.parts for seg in skip_segments))


@pytest.mark.parametrize("module_path", _production_modules(), ids=lambda p: str(p.relative_to(PROD_ROOT.parent)))
def test_no_raw_wall_clock_in_production(module_path: Path) -> None:
    """Every CE production module either uses now_utc_naive() / resolve_clock()
    or is on the explicit allow-list."""
    rel = str(module_path.relative_to(PROD_ROOT.parent))
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(module_path))
    hits = _collect_callsites(tree)
    if not hits:
        return
    if rel in ALLOWLIST:
        # An allow-listed file may keep its wall-clock callsites.
        return
    formatted = "\n".join(f"  {rel}:{lineno}  {expr}" for lineno, expr in hits)
    pytest.fail(
        f"Wall-clock SPOT violation — {rel} reads the wall-clock directly:\n"
        f"{formatted}\n\n"
        f"Use datamimic_ce.domains.domain_core.runtime.now_utc_naive() or "
        f"resolve_clock(deterministic=...) instead, or add {rel!r} to the "
        f"allow-list in tests_ce/architecture/test_clock_drift_gate.py with "
        f"a comment explaining why."
    )
