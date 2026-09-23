"""Transport boundary for invoking runtime descriptor execution."""

from datamimic_ce.engine.runtime.api import create_run_session as _create_run_session
from datamimic_ce.engine.runtime.api import run as _run
from datamimic_ce.engine.runtime.contracts import RunRequest, RunResult, RunSession


def create_run_session(request: RunRequest) -> RunSession:
    return _create_run_session(request)


def run(request: RunRequest) -> RunResult:
    return _run(request)


__all__ = ["create_run_session", "run"]
