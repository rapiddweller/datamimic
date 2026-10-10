import io
import sys
from pathlib import Path

import pytest

from datamimic_ce.engine.io.exporters.core.exporter_state_manager import ExporterStateManager
from datamimic_ce.engine.io.exporters.diagnostics.console_exporter import ConsoleExporter
from datamimic_ce.engine.io.exporters.session import consume_exporters


class CountingBufferedStdout(io.TextIOWrapper):
    flush_calls = 0

    def flush(self) -> None:
        self.flush_calls += 1
        super().flush()


@pytest.mark.parametrize(
    ("rows", "expected"),
    [
        ([{"id": 1}, {"id": 2}], b"\nrows: {'id': 1}\nrows: {'id': 2}\n"),
        ([], b"\n"),
    ],
)
def test_successful_page_reaches_buffered_stdout_before_return(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rows: list[dict], expected: bytes
) -> None:
    output = tmp_path / "stdout.txt"
    with CountingBufferedStdout(output.open("wb"), encoding="utf-8") as stream:
        with monkeypatch.context() as patch:
            patch.setattr(sys, "stdout", stream)
            ConsoleExporter().consume(("rows", rows))

        # Pool termination can bypass normal stream closure; bytes must already be visible.
        assert output.read_bytes() == expected
        assert stream.flush_calls == 1


def test_native_write_error_skips_success_flush(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    failure = OSError("stdout write failed")

    class BrokenStdout(CountingBufferedStdout):
        def write(self, text: str) -> int:
            raise failure

    with BrokenStdout((tmp_path / "stdout.txt").open("wb"), encoding="utf-8") as stream:
        with monkeypatch.context() as patch:
            patch.setattr(sys, "stdout", stream)
            with pytest.raises(OSError) as caught:
                ConsoleExporter().consume(("rows", [{"id": 1}]))

        assert caught.value is failure
        assert stream.flush_calls == 0


def test_native_iteration_error_skips_success_flush(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    failure = RuntimeError("row iteration failed")

    def rows():
        yield {"id": 1}
        raise failure

    with CountingBufferedStdout((tmp_path / "stdout.txt").open("wb"), encoding="utf-8") as stream:
        with monkeypatch.context() as patch:
            patch.setattr(sys, "stdout", stream)
            with pytest.raises(RuntimeError) as caught:
                ConsoleExporter().consume(("rows", rows()))

        assert caught.value is failure
        assert stream.flush_calls == 0


@pytest.mark.parametrize("through_dispatch", [False, True], ids=["direct", "dispatch"])
def test_flush_failure_preserves_native_error_or_dispatch_cause(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, through_dispatch: bool
) -> None:
    failure = OSError("stdout flush failed")

    def fail_flush() -> None:
        raise failure

    with CountingBufferedStdout((tmp_path / "stdout.txt").open("wb"), encoding="utf-8") as stream:
        with monkeypatch.context() as patch:
            patch.setattr(sys, "stdout", stream)
            patch.setattr(stream, "flush", fail_flush)
            with pytest.raises(ValueError if through_dispatch else OSError) as caught:
                rows = [{"id": 1}]
                if through_dispatch:
                    consume_exporters(("rows", rows), rows, "rows", [], [ConsoleExporter()], ExporterStateManager(1))
                else:
                    ConsoleExporter().consume(("rows", rows))

        if through_dispatch:
            assert str(caught.value) == "Error in exporter ConsoleExporter: stdout flush failed"
            assert caught.value.__cause__ is failure
        else:
            assert caught.value is failure
