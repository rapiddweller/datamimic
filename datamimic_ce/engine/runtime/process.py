"""Best-effort process titles for the DATAMIMIC runtime.

``setproctitle`` provides the portable implementation for macOS and Linux.
Titles are observability only: an unavailable native extension must never
prevent a descriptor run from starting.
"""

from __future__ import annotations

import os
from collections.abc import Callable

_native_setproctitle: Callable[[str], None] | None
try:
    from setproctitle import setproctitle as native_setproctitle
except Exception:  # pragma: no cover - optional native boundary
    _native_setproctitle = None
else:
    _native_setproctitle = native_setproctitle


def set_process_title(title: str) -> None:
    """Set an OS-visible process title without affecting runtime correctness."""
    if _native_setproctitle is None:
        return
    try:
        _native_setproctitle(title)
    except Exception:
        return


def bootstrap_process_title() -> None:
    """Keep the environment stable when the native title extension is active."""
    os.environ.setdefault("SPT_NOENV", "1")


def set_main_process_title(task_id: str, descriptor: str) -> None:
    """Expose the active CE descriptor run in OS process listings."""
    set_process_title(
        f"datamimic-ce: main pid={os.getpid()} task={_short(task_id)} desc={_short(descriptor, 24)}"
    )


def set_generate_worker_process_title(
    worker_id: int,
    task_id: str,
    statement: str,
    chunk: tuple[int, int],
) -> None:
    """Expose a multiprocessing generation worker and its assigned chunk."""
    start, end = chunk
    set_process_title(
        f"datamimic-ce: worker gen[w{worker_id}] pid={os.getpid()} task={_short(task_id)} "
        f"stmt={_short(statement, 24)} chunk={start}-{end}"
    )


def _short(value: str, length: int = 8) -> str:
    return value[:length]
