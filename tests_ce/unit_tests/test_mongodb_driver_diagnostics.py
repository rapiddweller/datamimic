"""The diagnostic bootstrap reaches real spawned workers without command logging."""

import json
import os
import socket
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("enabled", [False, True])
def test_spawned_mongo_driver_diagnostics_are_scoped_and_sanitized(tmp_path: Path, enabled: bool) -> None:
    source = Path(__file__).resolve().parents[2] / "script" / "mongodb_diagnostics"
    script = tmp_path / "probe.py"
    script.write_text(
        "import json, multiprocessing, os, sys\n"
        "from pymongo import MongoClient\n"
        "from pymongo.errors import ServerSelectionTimeoutError\n"
        "def probe(port):\n"
        "    with MongoClient('127.0.0.1', port, username='diagnostic-user', "
        "password='private-password-never-log', serverSelectionTimeoutMS=100, "
        "connectTimeoutMS=100) as client:\n"
        "        try:\n"
        "            client.admin.command('ping')\n"
        "        except ServerSelectionTimeoutError:\n"
        "            pass\n"
        "    return os.getpid()\n"
        "if __name__ == '__main__':\n"
        "    with multiprocessing.get_context('spawn').Pool(1) as pool:\n"
        "        worker = pool.apply(probe, (int(sys.argv[1]),))\n"
        "    print(json.dumps({'parent': os.getpid(), 'worker': worker}))\n",
        encoding="utf-8",
    )
    environment = {key: value for key, value in os.environ.items() if key != "DATAMIMIC_MONGODB_DIAGNOSTICS_DIR"}
    environment["PYTHONPATH"] = str(source)
    destination = tmp_path / "diagnostics"
    if enabled:
        environment["DATAMIMIC_MONGODB_DIAGNOSTICS_DIR"] = str(destination)
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        result = subprocess.run(
            [sys.executable, str(script), str(reservation.getsockname()[1])],
            cwd=tmp_path,
            env=environment,
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        )
    processes = json.loads(result.stdout)
    assert processes["worker"] != processes["parent"]
    if not enabled:
        assert not destination.exists()
        return
    log = destination / f"mongodb-driver-{processes['worker']}.log"
    assert log.is_file(), "driver diagnostics must be configured in the spawned worker"
    text = log.read_text(encoding="utf-8")
    assert f"pid={processes['worker']}" in text
    assert "Server selection failed" in text
    assert "Starting topology monitoring" in text
    assert "private-password-never-log" not in text
    assert "diagnostic-user" not in text
    assert "pymongo.command" not in text
