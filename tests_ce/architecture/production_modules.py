"""Production module listing shared by the architecture drift gates."""

from pathlib import Path

PROD_ROOT = Path(__file__).resolve().parents[2] / "datamimic_ce"


def production_modules() -> list[Path]:
    """Return every .py file under datamimic_ce/, sorted, excluding demos and __pycache__ paths."""
    skip_segments = {"demos", "__pycache__"}
    return sorted(p for p in PROD_ROOT.rglob("*.py") if not any(seg in p.parts for seg in skip_segments))
