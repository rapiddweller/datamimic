from datamimic_ce.utils import process_util


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
