from types import SimpleNamespace

from datamimic_ce.workers.generate_worker import GenerateWorker
from datamimic_ce.workers.multiprocessing_generate_worker import MultiprocessingGenerateWorker


def test_mp_wrapper_sets_title_before_generating(monkeypatch) -> None:
    context = SimpleNamespace(root=SimpleNamespace(task_id="task-123456789"))
    statement = SimpleNamespace(full_name="customer_generation")
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "datamimic_ce.utils.process_util.set_generate_worker_process_title",
        lambda **kwargs: captured.update(kwargs),
    )
    monkeypatch.setattr(GenerateWorker, "mp_preprocess", lambda *_: None)
    monkeypatch.setattr(
        GenerateWorker,
        "generate_and_export_data_by_chunk",
        lambda *_: {"customers": []},
    )

    result = MultiprocessingGenerateWorker.mp_wrapper((context, statement, 2, 100, 200, 50))

    assert result == {"customers": []}
    assert captured == {
        "worker_id": 2,
        "task_id": "task-123456789",
        "statement": "customer_generation",
        "chunk": (100, 200),
    }
