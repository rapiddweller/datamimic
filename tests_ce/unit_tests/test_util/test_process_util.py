import logging
from pathlib import Path

from datamimic_ce.engine.runtime import process_titles as process_util
from datamimic_ce.engine.runtime import logging as runtime_logging
from datamimic_ce.engine.runtime.contracts import RunRequest
from datamimic_ce.engine.runtime.lifecycle import runner


def test_set_main_process_title_uses_compact_runtime_context(monkeypatch) -> None:
    captured: list[str] = []

    monkeypatch.setattr(process_util.os, "getpid", lambda: 123)
    monkeypatch.setattr(process_util, "set_process_title", captured.append)

    process_util.set_main_process_title("abcdef123", "large_descriptor_name.xml")

    assert captured == ["datamimic-ce: main pid=123 task=abcdef12 desc=large_descriptor_name.xm"]


def test_set_generate_worker_process_title_includes_worker_and_chunk(monkeypatch) -> None:
    captured: list[str] = []

    monkeypatch.setattr(process_util.os, "getpid", lambda: 456)
    monkeypatch.setattr(process_util, "set_process_title", captured.append)

    process_util.set_generate_worker_process_title(
        worker_id=2,
        task_id="abcdef123",
        statement="customer_generation",
        chunk=(100, 200),
    )

    assert captured == [
        "datamimic-ce: worker gen[w2] pid=456 task=abcdef12 stmt=customer_generation chunk=100-200"
    ]


def test_set_process_title_ignores_unavailable_native_extension(monkeypatch) -> None:
    monkeypatch.setattr(process_util, "_native_setproctitle", None)

    process_util.set_process_title("datamimic-ce: main")


def test_set_process_title_ignores_native_extension_failure(monkeypatch) -> None:
    def fail(_title: str) -> None:
        raise RuntimeError("native process title unavailable")

    monkeypatch.setattr(process_util, "_native_setproctitle", fail)

    process_util.set_process_title("datamimic-ce: main")


def test_run_session_bootstraps_and_names_main_process_before_logging(monkeypatch) -> None:
    events: list[str] = []
    monkeypatch.setattr(runner, "bootstrap_process_title", lambda: events.append("bootstrap"))
    monkeypatch.setattr(
        runner,
        "set_main_process_title",
        lambda task_id, descriptor: events.append(f"title:{task_id}:{descriptor}"),
    )
    monkeypatch.setattr(runner, "setup_logger", lambda **_kwargs: events.append("logger"))
    monkeypatch.setattr(runner, "log_system_info", lambda: None)
    monkeypatch.setattr(runner, "log_memory_info", lambda _root: None)

    request = RunRequest(
        task_id="task-123",
        descriptor_path=Path(__file__),
        log_level=logging.INFO,
        platform_configs=None,
    )
    runner.RuntimeRunSession(request)

    assert events == ["bootstrap", f"title:task-123:{Path(__file__).name}", "logger"]


def test_repeated_logger_setup_keeps_existing_single_stream_handler(monkeypatch) -> None:
    logger = logging.getLogger("DATAMIMIC_TEST_REPEATED_SETUP")
    original_handlers = list(logger.handlers)
    original_level = logger.level
    original_propagate = logger.propagate
    monkeypatch.setattr(logging, "_nameToLevel", logging._nameToLevel.copy())
    monkeypatch.setattr(logging, "_levelToName", logging._levelToName.copy())

    try:
        runtime_logging.setup_logger(logger.name, "MAIN", level=25)
        first_handlers = [handler for handler in logger.handlers if isinstance(handler, logging.StreamHandler)]
        runtime_logging.setup_logger(logger.name, "MAIN", level=logging.INFO)
        second_handlers = [handler for handler in logger.handlers if isinstance(handler, logging.StreamHandler)]

        assert len(first_handlers) == len(second_handlers) == 1
        assert second_handlers[0] is first_handlers[0]
        assert logger.level == 25
    finally:
        for handler in list(logger.handlers):
            if handler not in original_handlers:
                logger.removeHandler(handler)
                handler.close()
        logger.setLevel(original_level)
        logger.propagate = original_propagate
