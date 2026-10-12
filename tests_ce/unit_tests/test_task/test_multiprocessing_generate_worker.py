from types import SimpleNamespace

from datamimic_ce.engine.runtime.tasks.generate.workers import multiprocessing_generate_worker as worker_module
from datamimic_ce.engine.runtime.tasks.generate.workers.generate_worker import GenerateWorker
from datamimic_ce.engine.runtime.tasks.generate.workers.multiprocessing_generate_worker import (
    MultiprocessingGenerateWorker,
)


def test_mp_wrapper_sets_title_before_generating(monkeypatch) -> None:
    context = SimpleNamespace(root=SimpleNamespace(task_id="task-123456789"))
    payload = object()
    statement = SimpleNamespace(full_name="customer_generation")
    events: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "datamimic_ce.engine.runtime.process_titles.set_generate_worker_process_title",
        lambda **kwargs: events.append(("title", kwargs)),
    )
    monkeypatch.setattr(GenerateWorker, "deserialize_worker_context", lambda value: context)
    monkeypatch.setattr(GenerateWorker, "cleanup_worker_context", lambda value: events.append(("cleanup", value)))
    monkeypatch.setattr(GenerateWorker, "mp_preprocess", lambda *_: events.append(("preprocess", None)))
    monkeypatch.setattr(
        GenerateWorker,
        "generate_and_export_data_by_chunk",
        lambda *_: events.append(("generate", None)) or {"customers": []},
    )

    result = MultiprocessingGenerateWorker.mp_wrapper((payload, statement, 2, 100, 200, 50))

    assert result == {"customers": []}
    assert events == [
        (
            "title",
            {
                "worker_id": 2,
                "task_id": "task-123456789",
                "statement": "customer_generation",
                "chunk": (100, 200),
            },
        ),
        ("preprocess", None),
        ("generate", None),
        ("cleanup", context),
    ]


def test_mp_process_uses_spawn_context(monkeypatch) -> None:
    events: list[object] = []

    class Pool:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def map(self, _function, args):
            events.append(len(args))
            return [{"rows": [index]} for index in range(len(args))]

    class Context:
        def Pool(self, processes: int):
            events.append(processes)
            return Pool()

    monkeypatch.setattr(worker_module.multiprocessing, "get_context", lambda method: events.append(method) or Context())

    result = MultiprocessingGenerateWorker().mp_process(object(), object(), [(0, 1), (1, 2)], page_size=1)

    assert events == ["spawn", 2, 2]
    assert result == {"rows": [0, 1]}
