# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

from pathlib import Path

import pytest

from datamimic_ce.engine.runtime.contracts import RunRequest
from datamimic_ce.engine.runtime.lifecycle.runner import RuntimeRunSession
from datamimic_ce.errors import OperationError

_DESCRIPTOR = '<setup rngSeed="7"><generate name="cities" count="3"><key name="n" constant="a"/></generate></setup>'


def _session(tmp_path: Path, *, test_mode: bool = True) -> RuntimeRunSession:
    descriptor = tmp_path / "datamimic.xml"
    descriptor.write_text(_DESCRIPTOR, encoding="utf-8")
    return RuntimeRunSession(RunRequest(descriptor_path=descriptor, test_mode=test_mode))


def test_second_execute_raises_and_keeps_first_capture(tmp_path: Path) -> None:
    session = _session(tmp_path)
    session.execute()
    first = session.capture_test_result()

    with pytest.raises(OperationError, match="executes once"):
        session.execute()

    assert session.capture_test_result() == first
    assert first is not None and len(first["cities"]) == 3


def test_fresh_session_per_run_is_unaffected(tmp_path: Path) -> None:
    first = _session(tmp_path)
    second = _session(tmp_path)
    first.execute()
    second.execute()

    assert first.capture_test_result() == second.capture_test_result()


def test_failed_first_execute_still_consumes_the_session(tmp_path: Path) -> None:
    session = _session(tmp_path)
    (tmp_path / "datamimic.xml").write_text("<setup><generate", encoding="utf-8")
    with pytest.raises(Exception) as first:
        session.execute()

    with pytest.raises(OperationError, match="executes once"):
        session.execute()
    assert not isinstance(first.value, OperationError)
