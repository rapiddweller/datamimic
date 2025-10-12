from __future__ import annotations

import os
import re
from pathlib import Path

from datamimic_ce.logger import logger

"""
Centralized helpers for locating domain datasets.

WHY: Many modules were using `Path(__file__).parents[3] / "domain_data" / ...`.
This is brittle and duplicated (violates SPOT/DRY). We provide a single
resolution function so paths are easy to maintain and extend (e.g., env override).
"""


DOMAIN_DATA_DIRNAME = "domain_data"

# Track which dataset codes we already logged fallback for, to avoid log spam
_logged_dataset_fallbacks: set[str] = set()


def _strict_dataset_mode() -> bool:
    """Return True when strict dataset mode is enabled.

    In strict mode (env `DATAMIMIC_STRICT_DATASET`), dataset fallbacks are
    disabled and missing dataset-suffixed files should surface as errors.
    """
    val = os.getenv("DATAMIMIC_STRICT_DATASET", "").strip()
    if not val:
        return False
    return val not in ("0", "false", "False")


def is_strict_dataset_mode() -> bool:
    """Public helper so callers can respect strict dataset mode."""

    return _strict_dataset_mode()


def repo_root(start: Path | None = None) -> Path:
    """Return repository root inferred from a file location.

    - Prefer `DATAMIMIC_ROOT` env var if provided.
    - Fallback: walk up until a directory containing `pyproject.toml` is found.
      If none found, use the third parent as previous behavior for compatibility.
    """
    env_root = os.getenv("DATAMIMIC_ROOT")
    if env_root:
        p = Path(env_root).expanduser().resolve()
        if p.exists():
            return p

    cur = (start or Path(__file__)).resolve()
    for ancestor in [cur, *cur.parents]:
        if (ancestor / "pyproject.toml").exists():
            return ancestor

    # Fallback to previous assumption to avoid breaking callers
    try:
        return cur.parents[3]
    except IndexError:
        return cur.anchor and Path(cur.anchor) or cur.parents[-1]


def domain_data_root(start: Path | None = None) -> Path:
    """Return the absolute path to the `domain_data` directory.

    Resolution order (first match wins):
      1. `DATAMIMIC_DOMAIN_DATA` env var (absolute path)
      2. Walk up from `start` and return `<ancestor>/domain_data` if exists
      3. Packaged location: `<repo>/datamimic_ce/domains/domain_data` if exists
      4. Default: `<repo>/domain_data`
    """
    env_data = os.getenv("DATAMIMIC_DOMAIN_DATA")
    if env_data:
        p = Path(env_data).expanduser().resolve()
        return p

    cur = (start or Path(__file__)).resolve()
    for ancestor in [cur, *cur.parents]:
        candidate = ancestor / DOMAIN_DATA_DIRNAME
        if candidate.exists():
            return candidate

    root = repo_root(start)
    packaged = root / "datamimic_ce" / "domains" / DOMAIN_DATA_DIRNAME
    if packaged.exists():
        return packaged

    return root / DOMAIN_DATA_DIRNAME


def dataset_path(*relative: str | os.PathLike[str], start: Path | None = None) -> Path:
    """Build a path under `domain_data` in a unified way.

    Example:
        dataset_path("healthcare", "medical", f"devices_{dataset}.csv")
    """
    root = domain_data_root(start)
    parts = list(map(str, relative))
    path = root.joinpath(*parts)

    # Smart fallback: if a dataset-suffixed file (e.g., name_CC.csv) is missing, fall back to _US
    #  Tests and runtime expect US as universal fallback when a specific dataset is not available.
    # Respect strict mode (DATAMIMIC_STRICT_DATASET) to disable this behavior for validation/testing.
    if parts:
        last = parts[-1]
        m = re.match(r"^(?P<stem>.+)_(?P<cc>[A-Z]{2})(?P<ext>\.[A-Za-z0-9._-]+)$", last)
        if m and not path.exists() and not _strict_dataset_mode():
            cc = m.group("cc").upper()
            if cc != "US":
                fallback_name = f"{m.group('stem')}_US{m.group('ext')}"
                fallback_path = root.joinpath(*parts[:-1], fallback_name)
                if fallback_path.exists():
                    # Log once per dataset code to avoid flooding logs
                    if cc not in _logged_dataset_fallbacks:
                        logger.warning(
                            "Dataset '%s' file '%s' not found; falling back to US dataset.",
                            cc,
                            last,
                        )
                        _logged_dataset_fallbacks.add(cc)
                    return fallback_path

    return path
