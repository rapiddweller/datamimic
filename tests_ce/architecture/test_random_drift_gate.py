"""RNG drift gate.

AST-walks the CE production tree and fails if any production module
draws randomness through the bare ``random`` module instead of an RNG
resolved via ``datamimic_ce.domains.domain_core.runtime.rng``.

Forbidden patterns (anywhere in ``datamimic_ce/**`` except the
allow-list below):

* ``random.<method>(...)`` where ``<method>`` is any callable on the
  stdlib ``random`` module that consumes / mutates global RNG state
  (``random``, ``choice``, ``choices``, ``randint``, ``sample``,
  ``shuffle``, ``uniform``, ``gauss``, ``triangular``,
  ``betavariate``, ``gammavariate``, ``lognormvariate``,
  ``normalvariate``, ``paretovariate``, ``vonmisesvariate``,
  ``weibullvariate``, ``expovariate``, ``seed``, ``randrange``,
  ``getrandbits``).
* ``from random import <name>`` of any of the above.

Instance methods on a ``Random`` object (``self._rng.choice(...)``,
``rng.choice(...)``) are allowed — that is the sanctioned path. Importing
the ``Random`` class itself is allowed (that's instance use).

The allow-list captures intentional exceptions:

* ``rng.py`` — the SPOT itself; defines the forking primitives.
* ``geniter_context.py`` — its ``.rng`` property returns the ``random``
  module when unseeded (so call-time callers don't branch on None).

Adding a new ``random.X(...)`` callsite means either (a) routing it
through ``ctx.rng`` (call time) / ``setup_ctx.derive_seeded_rng()``
(construction time) / a ``Random`` instance, or (b) adding the file to
the allow-list with a comment explaining why.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PROD_ROOT = Path(__file__).resolve().parents[2] / "datamimic_ce"

# Files allowed to draw from the bare ``random`` module. Keep this list
# small; every entry is a discipline exception that future reviewers
# should verify still applies.
ALLOWLIST: set[str] = {
    # SPOT itself: defines spawn_rng / derive_child_seed forking primitives.
    "datamimic_ce/domains/domain_core/runtime/rng.py",
    # GenIterContext.rng returns the random module when no seed is set
    # so call-time callers can use a single API without branching on None.
    "datamimic_ce/contexts/geniter_context.py",
    # PasswordGenerator deliberately uses secrets.choice for the character
    # picks; the final random.shuffle is the same intent (unpredictable
    # output regardless of <setup rngSeed>). Determinism is explicitly
    # not a contract for this generator.
    "datamimic_ce/domains/common/literal_generators/password_generator.py",
}

# Callables on the ``random`` module that consume / mutate global RNG state.
FORBIDDEN_RANDOM_FUNCS = {
    "random",
    "choice",
    "choices",
    "randint",
    "sample",
    "shuffle",
    "uniform",
    "gauss",
    "triangular",
    "betavariate",
    "gammavariate",
    "lognormvariate",
    "normalvariate",
    "paretovariate",
    "vonmisesvariate",
    "weibullvariate",
    "expovariate",
    "seed",
    "randrange",
    "getrandbits",
}


def _collect_callsites(tree: ast.AST) -> list[tuple[int, str]]:
    """Return ``(lineno, expr)`` for each forbidden ``random``-module hit."""
    hits: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        # random.<func>(...) — bare-name receiver only. An attribute
        # lookup whose receiver is something else (``self._rng.choice``,
        # ``rng.choice``, ``foo.random.choice``) is allowed.
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in FORBIDDEN_RANDOM_FUNCS
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "random"
        ):
            hits.append((node.lineno, f"random.{node.func.attr}(...)"))
        # from random import <forbidden>
        elif isinstance(node, ast.ImportFrom) and node.module == "random":
            for alias in node.names:
                if alias.name in FORBIDDEN_RANDOM_FUNCS:
                    hits.append((node.lineno, f"from random import {alias.name}"))
    return hits


def _production_modules() -> list[Path]:
    """Return every .py file under datamimic_ce/, sorted, excluding
    demos and any test/__pycache__ paths."""
    skip_segments = {"demos", "__pycache__"}
    return sorted(p for p in PROD_ROOT.rglob("*.py") if not any(seg in p.parts for seg in skip_segments))


@pytest.mark.parametrize("module_path", _production_modules(), ids=lambda p: str(p.relative_to(PROD_ROOT.parent)))
def test_no_raw_random_module_in_production(module_path: Path) -> None:
    """Every CE production module draws randomness through a resolved RNG
    or is on the explicit allow-list."""
    rel = str(module_path.relative_to(PROD_ROOT.parent))
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(module_path))
    hits = _collect_callsites(tree)
    if not hits:
        return
    if rel in ALLOWLIST:
        # An allow-listed file may keep its bare-module random callsites.
        return
    formatted = "\n".join(f"  {rel}:{lineno}  {expr}" for lineno, expr in hits)
    pytest.fail(
        f"RNG SPOT violation — {rel} draws from the bare random module:\n"
        f"{formatted}\n\n"
        f"Use ctx.rng (call time), setup_ctx.derive_seeded_rng() "
        f"(construction time), or a Random instance instead, or add "
        f"{rel!r} to the allow-list in "
        f"tests_ce/architecture/test_random_drift_gate.py with a comment "
        f"explaining why."
    )
