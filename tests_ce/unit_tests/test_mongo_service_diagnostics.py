"""CI diagnostics must follow spawn workers without exposing Mongo payloads."""

import http.client
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from tests_ce.service_diagnostics import mongo_diagnostics

DIAGNOSTICS = Path(__file__).resolve().parents[1] / "service_diagnostics"


def test_bootstrap_follows_spawn_and_preserves_source_and_native_timeout(tmp_path):
    program = tmp_path / "spawn_check.py"
    program.write_text(
        "import multiprocessing, os\n"
        "from pathlib import Path\n"
        "import datamimic_ce\n"
        "from pymongo import MongoClient\n"
        "def child():\n"
        "    client = MongoClient('localhost', 1, connect=False)\n"
        "    assert client.options.server_selection_timeout == 30\n"
        "    client.close()\n"
        "if __name__ == '__main__':\n"
        "    assert Path(datamimic_ce.__file__).resolve().is_relative_to(Path.cwd())\n"
        "    worker = multiprocessing.get_context('spawn').Process(target=child)\n"
        "    worker.start()\n"
        "    worker.join(20)\n"
        "    assert worker.exitcode == 0\n"
    )
    output = tmp_path / "events"
    env = dict(os.environ, MONGO_DIAGNOSTICS_DIR=str(output), PYTHONPATH=f"{DIAGNOSTICS}{os.pathsep}{Path.cwd()}")
    result = subprocess.run([sys.executable, str(program)], env=env, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    records = [json.loads(line) for file in output.glob("events-*.jsonl") for line in file.read_text().splitlines()]
    worker_pids = {row["pid"] for row in records if row["event"] == "TopologyOpenedEvent"}
    assert worker_pids, "the spawned worker must report its client topology"
    assert worker_pids <= {row["pid"] for row in records if row["event"] == "process_start"}


def test_event_and_service_metadata_drop_payloads_and_exception_text(tmp_path):
    from types import SimpleNamespace

    event = SimpleNamespace(
        connection_id=("mongo", 27017),
        server_address=("mongo", 27017),
        reason="error",
        failure=RuntimeError("password=secret document=private"),
        command={"insert": "private"},
        reply={"private": "secret"},
    )
    metadata = mongo_diagnostics.event_metadata(event)
    assert metadata["connection_id"] == ("mongo", 27017)
    assert metadata["server_address"] == ("mongo", 27017)
    assert metadata["reason"] == "error"
    assert "reason" not in mongo_diagnostics.event_metadata(SimpleNamespace(reason="password=secret"))
    assert metadata["failure_type"] == "RuntimeError"
    service = mongo_diagnostics.service_metadata(
        {
            "t": {"$date": "2026-10-15T00:00:00Z"},
            "s": "I",
            "c": "NETWORK",
            "id": 1,
            "ctx": "conn1",
            "msg": "password=secret",
            "attr": {"command": "private", "password": "secret"},
        }
    )
    assert service == {"t": {"$date": "2026-10-15T00:00:00Z"}, "s": "I", "c": "NETWORK", "id": 1, "ctx": "conn1"}
    assert "secret" not in json.dumps([metadata, service])


def test_runner_preserves_failure_exit_code_and_records_environment(tmp_path):
    failing_test = tmp_path / "test_failure.py"
    failing_test.write_text("def test_failure():\n    assert False\n")
    result = subprocess.run(
        [
            sys.executable,
            str(DIAGNOSTICS / "mongo_diagnostics.py"),
            "--output",
            str(tmp_path),
            "--",
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:rerunfailures",
            str(failing_test),
        ],
        text=True,
        capture_output=True,
        timeout=20,
    )
    assert result.returncode == 1, result.stderr
    metadata = json.loads((tmp_path / "environment.json").read_text())
    assert metadata["packages"]["pymongo"] == "4.10.1"
    assert metadata["test_exit_code"] == 1
    records = [json.loads(line) for file in tmp_path.glob("events-*.jsonl") for line in file.read_text().splitlines()]
    assert any(
        row["event"] == "test_start" and row["nodeid"].endswith("test_failure.py::test_failure") for row in records
    )
    assert any(row["event"] == "test_report" and row["outcome"] == "failed" for row in records)


def test_event_files_rotate_with_a_fixed_per_process_bound(tmp_path, monkeypatch):
    monkeypatch.setattr(mongo_diagnostics, "MAX_FILE_BYTES", 600)
    for index in range(20):
        mongo_diagnostics.emit(tmp_path, "test_event", index=index)
    files = list(tmp_path.glob("events-*.jsonl"))
    assert len(files) == 2
    assert all(file.stat().st_size <= 600 for file in files)
    records = [json.loads(line) for file in files for line in file.read_text().splitlines()]
    assert max(row["index"] for row in records) == 19


def test_unavailable_probe_is_distinct_from_the_test_exit_status(tmp_path):
    # Reserve a loopback port without listening, giving a controlled refusal.
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        result = subprocess.run(
            [
                sys.executable,
                str(DIAGNOSTICS / "mongo_diagnostics.py"),
                "--output",
                str(tmp_path),
                "--mongo-host",
                "127.0.0.1",
                "--mongo-port",
                str(reserved.getsockname()[1]),
                "--",
                sys.executable,
                "-c",
                "import time; time.sleep(3); raise SystemExit(9)",
            ],
            text=True,
            capture_output=True,
            timeout=15,
        )
    assert result.returncode == 9, result.stderr
    records = [json.loads(line) for file in tmp_path.glob("events-*.jsonl") for line in file.read_text().splitlines()]
    assert any(
        row["event"] == "authenticated_ping"
        and row["ok"] is False
        and row["error_type"] == "ServerSelectionTimeoutError"
        for row in records
    )


@pytest.mark.parametrize("fault", ["snapshot-before", "snapshot-after", "metadata-write", "metadata-directory"])
def test_diagnostic_faults_preserve_test_execution_and_exit_status(tmp_path, monkeypatch, capsys, fault):
    output = tmp_path / "diagnostics"
    marker = tmp_path / "executed"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "mongo_diagnostics",
            "--output",
            str(output),
            "--",
            sys.executable,
            "-c",
            "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('ran'); raise SystemExit(7)",
            str(marker),
        ],
    )
    if fault.startswith("snapshot"):

        def snapshot(output, container_id, phase):
            if fault == f"snapshot-{phase}":
                raise http.client.BadStatusLine("private diagnostic response")

        monkeypatch.setattr(mongo_diagnostics, "snapshot_service", snapshot)
    elif fault == "metadata-write":
        original = Path.write_text

        def write(path, *args, **kwargs):
            if path.name == "environment.json":
                raise OSError("private diagnostic response")
            return original(path, *args, **kwargs)

        monkeypatch.setattr(Path, "write_text", write)
    else:
        original = Path.mkdir

        def mkdir(path, *args, **kwargs):
            if path == output:
                raise OSError("private diagnostic response")
            return original(path, *args, **kwargs)

        monkeypatch.setattr(Path, "mkdir", mkdir)
    assert mongo_diagnostics.main() == 7
    assert marker.read_text() == "ran"
    assert "private diagnostic response" not in capsys.readouterr().err
