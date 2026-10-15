"""Collect metadata for #281 without changing runtime clients or test outcomes.

Only this CI runner adds the adjacent sitecustomize directory to PYTHONPATH.
Mongo commands, documents, credentials and exception messages are never recorded.
"""

import argparse
import hashlib
import http.client
import importlib.metadata
import json
import os
import socket
import struct
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from pymongo import MongoClient, monitoring
from pymongo.topology_description import TopologyDescription

MAX_FILE_BYTES = 1024 * 1024
WRITE_LOCK = threading.Lock()


@contextmanager
def best_effort(output, operation):
    try:
        yield
    except Exception as error:
        emit(output, "diagnostic_failed", operation=operation, error_type=type(error).__name__)


def emit(output, event, **fields):
    record = {
        "time": datetime.now(timezone.utc).isoformat(),
        "monotonic": time.monotonic(),
        "pid": os.getpid(),
        "ppid": os.getppid(),
        "thread": threading.get_ident(),
        "event": event,
        **fields,
    }
    try:
        line = json.dumps(record) + "\n"
        path = Path(output) / f"events-{os.getpid()}.jsonl"
        with WRITE_LOCK:
            if path.exists() and path.stat().st_size + len(line.encode()) > MAX_FILE_BYTES:
                path.replace(path.with_suffix(".previous.jsonl"))
            with path.open("a") as stream:
                stream.write(line)
    except OSError as error:
        print(f"Mongo diagnostics write failed: {type(error).__name__}", file=sys.stderr)


def event_metadata(event):
    fields = {}
    for name in ("connection_id", "address", "server_address", "duration", "awaited"):
        value = getattr(event, name, None)
        if isinstance(value, (str, int, float, bool, tuple)):
            fields[name] = value
    reason = getattr(event, "reason", None)
    if isinstance(reason, str) and reason in {"stale", "idle", "error", "poolClosed", "timeout", "connectionError"}:
        fields["reason"] = reason
    topology_id = getattr(event, "topology_id", None)
    if topology_id is not None:
        fields["topology_id"] = str(topology_id)
    failure = getattr(event, "reply", None) if isinstance(event, monitoring.ServerHeartbeatFailedEvent) else None
    failure = getattr(event, "failure", failure)
    if failure is not None:
        fields["failure_type"] = type(failure).__name__
    description = getattr(event, "new_description", None)
    if isinstance(description, TopologyDescription):
        fields["topology_type"] = description.topology_type_name
        fields["servers"] = [
            {
                "address": address,
                "type": server.server_type_name,
                "error_type": type(server.error).__name__ if server.error is not None else None,
            }
            for address, server in description.server_descriptions().items()
        ]
    elif description is not None:
        fields["server_type"] = description.server_type_name
        fields["error_type"] = type(description.error).__name__ if description.error is not None else None
    return fields


class MetadataListener(
    monitoring.TopologyListener,
    monitoring.ServerListener,
    monitoring.ServerHeartbeatListener,
    monitoring.ConnectionPoolListener,
):
    def record(self, event):
        emit(os.environ["MONGO_DIAGNOSTICS_DIR"], type(event).__name__, **event_metadata(event))

    opened = description_changed = closed = record
    started = succeeded = failed = record
    pool_created = pool_ready = pool_cleared = pool_closed = record
    connection_created = connection_ready = connection_closed = record
    connection_check_out_started = connection_check_out_failed = record
    connection_checked_out = connection_checked_in = record


def install_monitoring():
    output = os.environ["MONGO_DIAGNOSTICS_DIR"]
    with best_effort(output, "monitoring_bootstrap"):
        Path(output).mkdir(parents=True, exist_ok=True)
        monitoring.register(MetadataListener())
        emit(output, "process_start")


def pytest_runtest_logstart(nodeid, location):
    emit(os.environ["MONGO_DIAGNOSTICS_DIR"], "test_start", nodeid=nodeid)


def pytest_runtest_logreport(report):
    emit(
        os.environ["MONGO_DIAGNOSTICS_DIR"],
        "test_report",
        nodeid=report.nodeid,
        phase=report.when,
        outcome=report.outcome,
        duration=report.duration,
    )


def service_metadata(record):
    # Mongo's numeric log ID identifies the event; msg/attr can contain payloads.
    return {key: record[key] for key in ("t", "s", "c", "id", "ctx") if key in record}


class DockerConnection(http.client.HTTPConnection):
    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect("/var/run/docker.sock")


def docker_get(path):
    connection = DockerConnection("localhost", timeout=5)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        if response.status != 200:
            raise RuntimeError(f"docker_http_{response.status}")
        return response.read(16 * 1024 * 1024)
    finally:
        connection.close()


def snapshot_service(output, container_id, phase):
    if not container_id:
        return
    try:
        info = json.loads(docker_get(f"/containers/{container_id}/json"))
        state = info["State"]
        safe = {key: state[key] for key in ("Status", "Running", "OOMKilled", "ExitCode", "StartedAt", "FinishedAt")}
        safe.update(image_id=info["Image"], restart_count=info["RestartCount"])
        safe["health"] = state.get("Health", {}).get("Status")
        (output / f"service-{phase}.json").write_text(json.dumps(safe, indent=2) + "\n")
        data = docker_get(f"/containers/{container_id}/logs?stdout=1&stderr=1&tail=20000")
        chunks = []
        while len(data) >= 8:
            length = struct.unpack(">I", data[4:8])[0]
            chunks.append(data[8 : 8 + length])
            data = data[8 + length :]
        records = []
        for line in b"".join(chunks).splitlines():
            try:
                records.append(service_metadata(json.loads(line)))
            except (ValueError, TypeError):
                continue
        (output / f"service-log-{phase}.jsonl").write_text("".join(json.dumps(row) + "\n" for row in records))
    except (OSError, http.client.HTTPException, RuntimeError, ValueError, KeyError) as error:
        emit(output, "service_snapshot_failed", phase=phase, error_type=type(error).__name__)


def sample_ping(output, host, port, stop):
    # These bounds apply only to the independent diagnostic probe, never to tests.
    with MongoClient(
        host,
        port,
        username="datamimic",
        password="datamimic",
        authSource="admin",
        serverSelectionTimeoutMS=2000,
        connectTimeoutMS=2000,
        socketTimeoutMS=2000,
    ) as client:
        while not stop.is_set():
            start = time.monotonic()
            try:
                client.admin.command("ping")
                emit(output, "authenticated_ping", ok=True, elapsed=time.monotonic() - start)
            except Exception as error:
                emit(
                    output,
                    "authenticated_ping",
                    ok=False,
                    elapsed=time.monotonic() - start,
                    error_type=type(error).__name__,
                )
            stop.wait(2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mongo-host")
    parser.add_argument("--mongo-port", type=int, default=27017)
    parser.add_argument("--container-id")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("provide a test command after --")
    output = args.output.resolve()
    env = dict(os.environ, MONGO_DIAGNOSTICS_DIR=str(output))
    paths = [str(Path(__file__).resolve().parent), str(Path.cwd()), env.get("PYTHONPATH", "")]
    env["PYTHONPATH"] = os.pathsep.join(path for path in paths if path)
    env["PYTEST_PLUGINS"] = ",".join(filter(None, [env.get("PYTEST_PLUGINS"), "mongo_diagnostics"]))
    metadata = {}
    with best_effort(output, "environment_before"):
        output.mkdir(parents=True, exist_ok=True)
        metadata = {
            "python": sys.version,
            "packages": dict(
                sorted((dist.metadata["Name"].lower(), dist.version) for dist in importlib.metadata.distributions())
            ),
            "uv_lock_sha256": (
                hashlib.sha256(Path("uv.lock").read_bytes()).hexdigest() if Path("uv.lock").exists() else None
            ),
        }
        (output / "environment.json").write_text(json.dumps(metadata, indent=2) + "\n")
    with best_effort(output, "service_before"):
        snapshot_service(output, args.container_id, "before")
    stop = threading.Event()
    probe = None
    if args.mongo_host:
        probe = threading.Thread(target=sample_ping, args=(output, args.mongo_host, args.mongo_port, stop), daemon=True)
        probe.start()
    try:
        result = subprocess.run(command, env=env)
    finally:
        stop.set()
        if probe is not None:
            probe.join(timeout=5)
        with best_effort(output, "service_after"):
            snapshot_service(output, args.container_id, "after")
    with best_effort(output, "environment_after"):
        metadata["test_exit_code"] = result.returncode
        (output / "environment.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
