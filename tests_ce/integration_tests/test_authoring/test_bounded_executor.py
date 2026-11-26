# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Real child-process trees must not survive a bounded-execution timeout."""  # noqa: E501

import os
import time

import psutil
import pytest

from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.diagnostics import AuthoringSystemDiagnosticCode
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest


@pytest.mark.integration
@pytest.mark.skipif(os.name not in {"posix", "nt"}, reason="requires POSIX process groups or Windows taskkill")
def test_timeout_terminates_worker_children_and_grandchildren(tmp_path):
    import json

    marker = tmp_path / "descendant-pids.json"
    grandchild = "import time; time.sleep(30)"
    child = (
        "import os,subprocess,sys,time,json;from pathlib import Path;"
        f'p=subprocess.Popen([sys.executable,"-c",{grandchild!r}]);'
        f"Path({str(marker)!r}).write_text(json.dumps([os.getpid(),p.pid]));time.sleep(30)"
    )
    script = f'import subprocess,sys,time\np=subprocess.Popen([sys.executable,"-c",{child!r}])\ntime.sleep(30)\n'
    (tmp_path / "spawn.scr.py").write_text(script)
    xml = '<setup><execute uri="spawn.scr.py"/></setup>'
    started = time.monotonic()
    result = CeBoundedExecutor(AuthoringWorkspaceContext(tmp_path)).execute(
        BoundedExecutionRequest(xml=xml, allow_side_effects=True, timeout_seconds=10)
    )
    assert time.monotonic() - started < 15
    assert not result.ok
    assert result.diagnostics[0].code is AuthoringSystemDiagnosticCode.TIMEOUT
    assert marker.exists(), "the descendant probe must actually execute before cancellation"
    # The leader is reaped at once; a descendant can still be exiting after the SIGKILL (#432).
    deadline = time.monotonic() + 5
    while (alive := [pid for pid in json.loads(marker.read_text()) if _running(pid)]) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not alive


def _running(pid):
    try:
        return psutil.Process(pid).status() != psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        return False


@pytest.mark.integration
@pytest.mark.skipif(os.name == "nt", reason="POSIX process groups only")
def test_timeout_stays_timeout_while_the_killed_group_is_still_exiting(tmp_path, monkeypatch):
    """macOS killpg returns EPERM when no member of the group is alive but one is not reaped yet (#432). That can
    occur at the SIGTERM and at the SIGKILL. Linux does not do this, so the fake sends the real signal and then
    gives that EPERM for each call."""
    import errno
    import signal
    from contextlib import suppress

    real_killpg = os.killpg
    sent = []

    def exiting_group(pgid, sig):
        sent.append(sig)
        with suppress(ProcessLookupError):
            real_killpg(pgid, sig)
        raise PermissionError(errno.EPERM, os.strerror(errno.EPERM))

    monkeypatch.setattr(os, "killpg", exiting_group)
    (tmp_path / "sleep.scr.py").write_text("import time\ntime.sleep(30)\n")
    result = CeBoundedExecutor(AuthoringWorkspaceContext(tmp_path)).execute(
        BoundedExecutionRequest(
            xml='<setup><execute uri="sleep.scr.py"/></setup>', allow_side_effects=True, timeout_seconds=2
        )
    )
    assert not result.ok
    assert result.diagnostics[0].code is AuthoringSystemDiagnosticCode.TIMEOUT
    assert sent == [signal.SIGTERM, signal.SIGKILL]
