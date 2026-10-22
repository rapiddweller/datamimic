"""The CE executor keeps complete evidence and owns private process resources."""

import base64
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath

import psutil
import pytest
from pydantic import SecretBytes

from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor, _snapshot_workspace
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.diagnostics import AuthoringSystemDiagnosticCode
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest
from datamimic_ce.errors import IssueCode, RuntimeConfigError

_XML = (
    '<setup rngSeed="7"><generate name="rows" count="3">'
    '<key name="id" generator="IncrementGenerator"/></generate></setup>'
)


def test_executor_keeps_full_capture_beyond_response_sample():
    result = CeBoundedExecutor().execute(BoundedExecutionRequest(xml=_XML))
    assert result.ok, result.diagnostics
    product = result.captured.get("rows")
    assert len(product.rows) == 3
    assert product.capture.observed == 3
    assert product.capture.complete
    assert result.smoke_export.requested is False


def test_hash_key_reaches_private_bounded_child_without_entering_public_evidence(tmp_path, monkeypatch):
    sentinel = b"DATAMIMIC_SENTINEL_" + b"x" * 20
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    request = BoundedExecutionRequest(
        xml=(
            '<setup><generate name="rows" count="1"><key name="token" constant="known" '
            "converter=\"Hash('sha256','hex')\"/></generate></setup>"
        )
    )
    key = SecretBytes(sentinel)
    result = CeBoundedExecutor().execute(request, pseudonymization_key=key)
    assert result.ok, result.diagnostics
    assert result.captured.get("rows").rows[0]["token"]
    assert sentinel.decode() not in repr(key)
    assert sentinel.decode() not in request.model_dump_json()
    assert sentinel.decode() not in repr(result)
    assert base64.b64encode(sentinel).decode("ascii") not in repr(result)
    assert list(tmp_path.iterdir()) == []


def test_invalid_external_key_keeps_typed_runtime_error_without_echoing_secret():
    secret = b"short-sentinel"

    with pytest.raises(RuntimeConfigError) as error:
        CeBoundedExecutor().execute(BoundedExecutionRequest(xml="<setup />"), pseudonymization_key=SecretBytes(secret))

    assert error.value.issue_code is IssueCode.RUNTIME_PSEUDONYMIZATION_KEY_INVALID
    assert secret.decode() not in str(error.value)


def test_child_exit_while_sending_private_input_returns_child_crash(monkeypatch):
    from datamimic_ce.authoring.adapters import bounded_executor

    real_popen = subprocess.Popen

    def exit_before_read(_command, **kwargs):
        return real_popen([sys.executable, "-c", "import os; os._exit(7)"], **kwargs)

    monkeypatch.setattr(bounded_executor.subprocess, "Popen", exit_before_read)
    result = CeBoundedExecutor().execute(
        BoundedExecutionRequest(xml="<setup />"),
        pseudonymization_key=SecretBytes(b"x" * 32),
    )

    assert not result.ok
    assert result.diagnostics[0].code is AuthoringSystemDiagnosticCode.CHILD_CRASH


def test_child_crash_remains_primary_when_tree_cleanup_fails(monkeypatch):
    from datamimic_ce.authoring.adapters import bounded_executor

    real_popen = subprocess.Popen

    def exit_before_read(_command, **kwargs):
        return real_popen([sys.executable, "-c", "import os; os._exit(7)"], **kwargs)

    def failed_cleanup(*_args, **_kwargs):
        return False

    monkeypatch.setattr(bounded_executor.subprocess, "Popen", exit_before_read)
    monkeypatch.setattr(bounded_executor, "_terminate_process_tree", failed_cleanup)
    result = CeBoundedExecutor().execute(
        BoundedExecutionRequest(xml="<setup />"),
        pseudonymization_key=SecretBytes(b"x" * 32),
    )

    assert not result.ok
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        AuthoringSystemDiagnosticCode.CHILD_CRASH,
        AuthoringSystemDiagnosticCode.CLEANUP,
    ]


def test_windows_tree_termination_keeps_success_after_worker_exit():
    from datamimic_ce.authoring.adapters import bounded_executor

    class Process:
        pid = 123

        def poll(self):
            return 0

        def wait(self, *, timeout):
            assert timeout > 0

    class Job:
        closed = 0

        def active_process_count(self):
            return 1

        def process_ids(self, _deadline):
            return (123,)

        def terminate(self):
            pytest.fail("an empty job must not be terminated")

        def close(self):
            self.closed += 1
            return True

    job = Job()
    assert bounded_executor._terminate_process_tree(Process(), windows_job=job)
    assert job.closed == 1


@pytest.mark.parametrize("descendants", [(456,), (456, 789)])
def test_windows_tree_termination_tracks_descendants_after_worker_exit(descendants):
    from datamimic_ce.authoring.adapters import bounded_executor

    class Process:
        pid = 123

        def poll(self):
            return 0

        def wait(self, *, timeout):
            return 0

    class Job:
        active = 1 + len(descendants)
        terminated = 0
        closed = 0

        def active_process_count(self):
            return self.active

        def process_ids(self, _deadline):
            return (123, *descendants) if self.active > 1 else (123,)

        def terminate(self):
            self.terminated += 1
            self.active = 0
            return True

        def close(self):
            self.closed += 1
            return True

    job = Job()
    assert bounded_executor._terminate_process_tree(Process(), windows_job=job)
    assert job.terminated == 1
    assert job.closed == 1


def test_windows_tree_query_failure_blocks_cleanup_success():
    from datamimic_ce.authoring.adapters import bounded_executor

    class Process:
        pid = 123

        def poll(self):
            return 0

        def wait(self, *, timeout):
            return 0

    class Job:
        queries = 0

        def active_process_count(self):
            self.queries += 1
            return None if self.queries == 1 else 1

        def process_ids(self, _deadline):
            return (123,)

        def terminate(self):
            return True

        def close(self):
            return True

    assert not bounded_executor._terminate_process_tree(Process(), windows_job=Job())


def test_windows_suspended_child_is_killed_when_job_assignment_fails(tmp_path, monkeypatch):
    from datamimic_ce.authoring.adapters import bounded_executor

    class Process:
        pid = 123
        stdin = None
        killed = False

        def kill(self):
            self.killed = True

        def wait(self, *, timeout):
            assert timeout > 0

        def poll(self):
            return 1 if self.killed else None

    class Job:
        closed = 0

        def assign(self, _process_id):
            return False

        def resume_suspended_process(self, _process_id):
            pytest.fail("a child outside the job must not resume")

        def close(self):
            self.closed += 1
            return True

    process = Process()
    job = Job()
    monkeypatch.setattr(bounded_executor, "_is_windows_platform", lambda: True)
    monkeypatch.setattr(bounded_executor, "WindowsProcessTree", lambda: job)
    monkeypatch.setattr(bounded_executor.subprocess, "Popen", lambda *_args, **_kwargs: process)

    result = bounded_executor.CeBoundedExecutor._execute_child(
        BoundedExecutionRequest(xml="<setup />"), tmp_path, tmp_path / "request", tmp_path / "reply", None
    )

    assert not result.ok
    assert result.diagnostics[0].code is AuthoringSystemDiagnosticCode.CHILD_CRASH
    assert process.killed
    assert job.closed == 1


def test_blocked_private_input_obeys_execution_timeout(monkeypatch):
    from datamimic_ce.authoring.adapters import bounded_executor

    real_popen = subprocess.Popen

    def do_not_read(_command, **kwargs):
        return real_popen([sys.executable, "-c", "import time; time.sleep(30)"], **kwargs)

    monkeypatch.setattr(bounded_executor.subprocess, "Popen", do_not_read)
    started = time.monotonic()
    result = CeBoundedExecutor().execute(
        BoundedExecutionRequest(xml="<setup />", timeout_seconds=1),
        pseudonymization_key=SecretBytes(b"x" * (4 * 1024 * 1024)),
    )

    assert time.monotonic() - started < 3
    assert not result.ok
    assert result.diagnostics[0].code is AuthoringSystemDiagnosticCode.TIMEOUT


def test_failed_private_bounded_child_does_not_return_key_material():
    sentinel = b"DATAMIMIC_SENTINEL_" + b"x" * 20
    request = BoundedExecutionRequest(
        xml=(
            '<setup><generate name="rows" count="1"><key name="token" constant="known" '
            "converter=\"Hash('unknown','hex')\"/></generate></setup>"
        )
    )

    result = CeBoundedExecutor().execute(request, pseudonymization_key=SecretBytes(sentinel))

    public_result = repr(result)
    assert not result.ok
    assert sentinel.decode() not in public_result
    assert base64.b64encode(sentinel).decode("ascii") not in public_result


def test_launcher_package_cannot_replace_the_selected_worker(tmp_path, monkeypatch):
    shadow = tmp_path / "datamimic_ce"
    shadow.mkdir()
    (shadow / "__init__.py").write_text('raise RuntimeError("wrong launcher package")\n')
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PYTHONPATH", str(Path(__file__).resolve().parents[3]))

    result = CeBoundedExecutor().execute(BoundedExecutionRequest(xml=_XML))

    assert result.ok, result.diagnostics
    assert result.captured.get("rows").rows == ({"id": 1}, {"id": 2}, {"id": 3})


def test_private_workspace_preserves_relative_sources_without_host_writes(tmp_path):
    folder = tmp_path / "nested"
    folder.mkdir()
    (folder / "rows.csv").write_text("id\n1\n2\n", encoding="utf-8")
    original = folder / "input.xml"
    original.write_text("original descriptor", encoding="utf-8")
    workspace = AuthoringWorkspaceContext(tmp_path, PurePosixPath("nested/input.xml"))
    xml = (
        '<setup rngSeed="7"><generate name="rows" source="rows.csv" separator="," '
        'distribution="ordered" target="JSON"/></setup>'
    )
    result = CeBoundedExecutor(workspace).execute(
        BoundedExecutionRequest(xml=xml, descriptor_path=workspace.descriptor_path, smoke_export=True)
    )
    assert result.ok, result.diagnostics
    assert result.captured.get("rows").rows == ({"id": "1"}, {"id": "2"})
    assert result.smoke_export.requested and result.smoke_export.failed_exporters == 0
    assert original.read_text() == "original descriptor"
    assert sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*")) == [
        "nested",
        "nested/input.xml",
        "nested/rows.csv",
    ]


@pytest.mark.parametrize("environment", [".venv", "venv"])
def test_snapshot_omits_root_python_environments_but_keeps_nested_resources(tmp_path, environment):
    source = tmp_path / "project"
    source.mkdir()
    (source / environment).mkdir()
    (source / environment / "private.txt").write_text("runtime-only")
    data = source / "data" / environment
    data.mkdir(parents=True)
    (data / "rows.csv").write_text("id\n1\n2\n")
    destination = tmp_path / "snapshot"

    _snapshot_workspace(source, destination)

    assert not (destination / environment).exists()
    assert (destination / "data" / environment / "rows.csv").read_text() == "id\n1\n2\n"


def test_project_root_with_python_environment_can_build_relative_sources(tmp_path):
    environment = tmp_path / ".venv" / "bin"
    environment.mkdir(parents=True)
    try:
        (environment / "python").symlink_to(sys.executable)
    except OSError:
        pytest.skip("native symlink privilege unavailable")
    data = tmp_path / "data"
    data.mkdir()
    (data / "rows.csv").write_text("id\n1\n2\n")

    result = CeBoundedExecutor(AuthoringWorkspaceContext(tmp_path)).execute(
        BoundedExecutionRequest(
            xml='<setup rngSeed="7"><generate name="rows" source="data/rows.csv" distribution="ordered">'
            '<key name="id" script="int(this.id)"/></generate></setup>'
        )
    )

    assert result.ok, result.diagnostics
    assert result.captured.get("rows").rows == ({"id": 1}, {"id": 2})
    assert (environment / "python").is_symlink()


def test_snapshot_rejects_symlinks(tmp_path):
    try:
        (tmp_path / "resource").symlink_to(tmp_path.parent)
    except OSError:
        pytest.skip("native symlink privilege unavailable; Windows junction control remains")
    result = CeBoundedExecutor(AuthoringWorkspaceContext(tmp_path)).execute(
        BoundedExecutionRequest(xml='<setup><generate name="rows" source="rows.csv"/></setup>')
    )
    assert not result.ok
    assert result.diagnostics[0].code is AuthoringSystemDiagnosticCode.ENVIRONMENT
    assert str(tmp_path) not in result.diagnostics[0].message


def test_bound_descriptor_mismatch_is_a_typed_failure(tmp_path):
    workspace = AuthoringWorkspaceContext(tmp_path, PurePosixPath("nested/input.xml"))
    result = CeBoundedExecutor(workspace).execute(BoundedExecutionRequest(xml=_XML))
    assert not result.ok
    assert result.diagnostics[0].code is AuthoringSystemDiagnosticCode.DESCRIPTOR


def test_runtime_uses_explicit_profile_loader(tmp_path, monkeypatch):
    from datamimic_ce.engine.dsl.api import DescriptorParser
    from datamimic_ce.engine.runtime.api import run
    from datamimic_ce.engine.runtime.contracts import RunRequest

    descriptor = tmp_path / "model.xml"
    descriptor.write_text("<setup/>")

    def loader(directory, environment):
        return {}

    original = DescriptorParser.parse
    observed = []

    def parse(*args, **kwargs):
        observed.append(kwargs["profile_loader"])
        return original(*args, **kwargs)

    monkeypatch.setattr(DescriptorParser, "parse", parse)
    run(RunRequest(descriptor_path=descriptor, profile_loader=loader))
    assert observed == [loader]


def test_workspace_profile_loader_has_no_home_or_cwd_fallback(tmp_path, monkeypatch):
    root = tmp_path / "workspace"
    root.mkdir()
    (tmp_path / "environment.env.properties").write_text("db.db.password=outside")
    monkeypatch.chdir(tmp_path)
    workspace = AuthoringWorkspaceContext(root)
    assert workspace.load_connection_profile(root, "environment") == {}
    with pytest.raises(ValueError):
        workspace.load_connection_profile(root, "../environment")


@pytest.mark.skipif(os.name not in {"posix", "nt"}, reason="requires supported process-tree ownership")
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
    for pid in json.loads(marker.read_text()):
        assert not psutil.pid_exists(pid) or psutil.Process(pid).status() == psutil.STATUS_ZOMBIE


def test_pure_descriptor_does_not_copy_unrelated_repository_files(tmp_path, monkeypatch):
    from datamimic_ce.authoring.adapters import bounded_executor

    def refuse_copy(*args):
        pytest.fail("a resource-free descriptor must not snapshot the host repository")

    monkeypatch.setattr(bounded_executor, "_snapshot_workspace", refuse_copy)
    (tmp_path / "unrelated-file").write_text("unrelated host repository data")
    result = CeBoundedExecutor(AuthoringWorkspaceContext(tmp_path)).execute(BoundedExecutionRequest(xml=_XML))
    assert result.ok, result.diagnostics


@pytest.mark.parametrize("resource", ["../outside.csv", "/private/tmp/outside.csv", r"..\outside.csv"])
def test_workspace_refuses_escaping_file_source(tmp_path, resource):
    xml = f'<setup><generate name="rows" source="{resource}"/></setup>'
    result = CeBoundedExecutor(AuthoringWorkspaceContext(tmp_path)).execute(BoundedExecutionRequest(xml=xml))
    assert not result.ok
    assert result.diagnostics[0].code is AuthoringSystemDiagnosticCode.ENVIRONMENT


def test_snapshot_bounds_are_enforced_without_relaxing_pure_mode(tmp_path, monkeypatch):
    from datamimic_ce.authoring.adapters import bounded_executor

    monkeypatch.setattr(bounded_executor, "_MAX_WORKSPACE_FILE_BYTES", 1)
    (tmp_path / "rows.csv").write_text("id\n1\n")
    xml = '<setup><generate name="rows" source="rows.csv"/></setup>'
    result = CeBoundedExecutor(AuthoringWorkspaceContext(tmp_path)).execute(BoundedExecutionRequest(xml=xml))
    assert result.diagnostics[0].code is AuthoringSystemDiagnosticCode.ENVIRONMENT


def test_snapshot_reads_file_identity_instead_of_windows_cached_entry_stat(tmp_path, monkeypatch):
    from contextlib import contextmanager

    from datamimic_ce.authoring.adapters import bounded_executor

    source = tmp_path / "workspace"
    source.mkdir()
    resource = source / "rows.csv"
    content = b"id\n1\n2\n"
    resource.write_bytes(content)
    original_scandir = os.scandir

    class WindowsCachedEntry:
        def __init__(self, entry):
            self.name = entry.name
            self.entry = entry

        def stat(self, *, follow_symlinks):
            actual = self.entry.stat(follow_symlinks=follow_symlinks)
            fields = list(actual)
            fields[1] = fields[2] = fields[3] = 0
            return os.stat_result(
                fields,
                {
                    "st_atime_ns": actual.st_atime_ns,
                    "st_mtime_ns": actual.st_mtime_ns,
                    "st_ctime_ns": actual.st_ctime_ns,
                },
            )

    @contextmanager
    def windows_cached_scandir(path):
        with original_scandir(path) as entries:
            yield (WindowsCachedEntry(entry) for entry in entries)

    monkeypatch.setattr(os, "scandir", windows_cached_scandir)
    bounded_executor._snapshot_workspace(source, tmp_path / "snapshot")
    assert (tmp_path / "snapshot" / "rows.csv").read_bytes() == content
    assert resource.read_bytes() == content


def test_snapshot_rejects_file_replaced_between_stat_and_open(tmp_path, monkeypatch):
    from datamimic_ce.authoring.adapters import bounded_executor

    source = tmp_path / "workspace"
    source.mkdir()
    resource = source / "rows.csv"
    resource.write_text("id\n1\n")
    original_open = os.open
    replaced = False

    def racing_open(path, flags, *args, **kwargs):
        nonlocal replaced
        if Path(path).name == "rows.csv" and not replaced:
            replaced = True
            previous = tmp_path / "previous-rows.csv"
            # Keep the old inode alive so replacement cannot reuse its identity.
            resource.rename(previous)
            resource.write_text("id\n2\n")
            before, after = previous.stat(), resource.stat()
            assert (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", racing_open)
    with pytest.raises(ValueError, match="changed before opening"):
        bounded_executor._snapshot_workspace(source, tmp_path / "snapshot")
    assert replaced


def test_missing_memstore_product_remains_keyerror_and_structured_across_child(tmp_path):
    import pickle

    from datamimic_ce.engine.io.memstore import Memstore
    from datamimic_ce.errors import MissingMemstoreProductError
    from datamimic_ce.errors.codes import ErrorCode

    with pytest.raises(KeyError) as caught:
        Memstore("mem").get_data_by_type("missing")
    error = caught.value
    assert isinstance(error, MissingMemstoreProductError)
    restored = pickle.loads(pickle.dumps(error))
    assert type(restored) is MissingMemstoreProductError
    assert restored.product_type == "missing" and restored.code is ErrorCode.INVALID_SOURCE
    assert isinstance(restored.__cause__, KeyError)
    xml = '<setup><memstore id="mem"/><generate name="rows" source="mem" type="missing" count="1"/></setup>'
    result = CeBoundedExecutor(AuthoringWorkspaceContext(tmp_path)).execute(BoundedExecutionRequest(xml=xml))
    assert not result.ok
    assert result.diagnostics[0].ce_error.error_code is ErrorCode.INVALID_SOURCE
    assert "missing" not in result.diagnostics[0].message


def test_inline_file_source_cannot_escape_private_workspace():
    result = CeBoundedExecutor().execute(
        BoundedExecutionRequest(xml='<setup><generate name="rows" source="/private/tmp/outside.csv"/></setup>')
    )
    assert result.diagnostics[0].code is AuthoringSystemDiagnosticCode.ENVIRONMENT


def test_bounded_transformer_forces_read_only_after_profile_resolution(tmp_path):
    from datamimic_ce.authoring.adapters.dryrun import neutralize_for_dry_run
    from datamimic_ce.engine.dsl.api import DatabaseStatement, DescriptorParser, MongoDBStatement

    xml = (
        '<setup><database id="db" dbms="postgresql" host="localhost" port="5432" '
        'database="test" user="test" password="test"/><mongodb id="mongo" host="localhost" '
        'port="27017" database="test"/></setup>'
    )
    root = DescriptorParser.parse_xml(xml, tmp_path / "model.xml", None, "production", profile_loader=lambda *_: {})
    clients = [
        statement for statement in root.sub_statements if isinstance(statement, (DatabaseStatement, MongoDBStatement))
    ]
    assert len(clients) == 2 and all(not statement.model.read_only for statement in clients)
    neutralize_for_dry_run(root, max_count=2, allow_side_effects=False)
    assert all(statement.model.read_only for statement in clients)


def test_real_sqlite_source_failure_keeps_ce_identity_in_private_child(tmp_path):
    import sqlite3

    from datamimic_ce.errors.codes import ErrorCode, IssueCode

    (tmp_path / "db").mkdir()
    connection = sqlite3.connect(tmp_path / "db" / "database.sqlite")
    connection.execute("CREATE TABLE present (id INTEGER)")
    connection.close()
    xml = (
        '<setup><database id="db" dbms="sqlite" database="database"/><generate name="rows" '
        'source="db" count="1" selector="SELECT private_column FROM absent"/></setup>'
    )
    result = CeBoundedExecutor(AuthoringWorkspaceContext(tmp_path)).execute(BoundedExecutionRequest(xml=xml))
    assert not result.ok
    assert result.diagnostics[0].code is AuthoringSystemDiagnosticCode.CHILD_EXECUTION
    assert result.diagnostics[0].ce_error.error_code is ErrorCode.OPERATION_ERROR
    assert result.diagnostics[0].ce_error.issue_code is IssueCode.OPERATION_EXECUTION_FAILED
    assert "private_column" not in result.diagnostics[0].message
    assert str(tmp_path) not in result.diagnostics[0].message


def test_child_crash_is_typed_and_does_not_wait_for_timeout(tmp_path):
    (tmp_path / "crash.py").write_text("import os\nos._exit(17)\n")
    started = time.monotonic()
    result = CeBoundedExecutor(AuthoringWorkspaceContext(tmp_path)).execute(
        BoundedExecutionRequest(
            xml='<setup><execute uri="crash.py"/></setup>', allow_side_effects=True, timeout_seconds=20
        )
    )
    assert time.monotonic() - started < 15
    assert not result.ok
    assert result.diagnostics[0].code is AuthoringSystemDiagnosticCode.CHILD_CRASH
    if os.name != "nt":
        assert "exit code 17" in result.diagnostics[0].message


def test_process_cleanup_failure_blocks_success_after_actual_reap(tmp_path, monkeypatch):
    from datamimic_ce.authoring.adapters import bounded_executor

    original = bounded_executor._terminate_process_tree

    def failed_cleanup(process, *args, **kwargs):
        original(process, *args, **kwargs)
        return False

    monkeypatch.setattr(bounded_executor, "_terminate_process_tree", failed_cleanup)
    result = CeBoundedExecutor().execute(BoundedExecutionRequest(xml=_XML))
    assert not result.ok
    assert result.diagnostics[0].code is AuthoringSystemDiagnosticCode.CLEANUP


def test_workspace_cleanup_failure_blocks_success_after_actual_removal(monkeypatch):
    import tempfile

    original = tempfile.TemporaryDirectory.cleanup

    def failed_cleanup(directory):
        original(directory)
        raise OSError("cleanup verification failed")

    monkeypatch.setattr(tempfile.TemporaryDirectory, "cleanup", failed_cleanup)
    result = CeBoundedExecutor().execute(BoundedExecutionRequest(xml=_XML))
    assert not result.ok
    assert result.diagnostics[0].code is AuthoringSystemDiagnosticCode.CLEANUP


def test_unique_reference_exhaustion_keeps_category_in_private_child(tmp_path):
    import sqlite3

    from datamimic_ce.errors import ErrorCode

    (tmp_path / "db").mkdir()
    with sqlite3.connect(tmp_path / "db" / "database.sqlite") as connection:
        connection.execute("CREATE TABLE items (id INTEGER)")
        connection.executemany("INSERT INTO items VALUES (?)", [(1,), (2,), (3,), (4,)])
    xml = (
        '<setup rngSeed="7"><database id="db" dbms="sqlite" database="database"/>'
        '<generate name="rows" count="5" pageSize="2"><condition><if condition="True">'
        '<reference name="fk" source="db" sourceType="items" sourceKey="id" unique="true"/>'
        "</if></condition></generate></setup>"
    )
    result = CeBoundedExecutor(AuthoringWorkspaceContext(tmp_path)).execute(BoundedExecutionRequest(xml=xml))
    assert not result.ok
    diagnostic = result.diagnostics[0]
    assert diagnostic.code is AuthoringSystemDiagnosticCode.CHILD_EXECUTION
    assert diagnostic.ce_error is not None
    assert diagnostic.ce_error.error_code is ErrorCode.TASK_CONFIG
    assert diagnostic.ce_error.issue_code is None


@pytest.mark.parametrize("primary", [RuntimeError("primary failure"), KeyboardInterrupt()])
def test_workspace_cleanup_preserves_primary_exception_after_actual_removal(monkeypatch, primary):
    import tempfile

    original = tempfile.TemporaryDirectory.cleanup
    removed = []

    def failed_cleanup(directory):
        original(directory)
        removed.append(Path(directory.name))
        raise OSError("cleanup verification failed")

    def failed_child(*args):
        raise primary

    monkeypatch.setattr(tempfile.TemporaryDirectory, "cleanup", failed_cleanup)
    monkeypatch.setattr(CeBoundedExecutor, "_execute_child", failed_child)
    with pytest.raises(type(primary)) as caught:
        CeBoundedExecutor().execute(BoundedExecutionRequest(xml=_XML))
    assert caught.value is primary
    assert len(removed) == 1
    assert not removed[0].exists()


@pytest.mark.parametrize("primary", [RuntimeError("primary failure"), KeyboardInterrupt()])
def test_process_cleanup_preserves_primary_exception_after_actual_reap(monkeypatch, primary):
    from datamimic_ce.authoring.adapters import bounded_executor

    original = bounded_executor._terminate_process_tree
    reaped = []

    def failed_cleanup(process, *args, **kwargs):
        original(process, *args, **kwargs)
        reaped.append(process)
        return False

    def failed_decode(*args):
        raise primary

    monkeypatch.setattr(bounded_executor, "_terminate_process_tree", failed_cleanup)
    monkeypatch.setattr(bounded_executor, "_decode_reply", failed_decode)
    with pytest.raises(type(primary)) as caught:
        CeBoundedExecutor().execute(BoundedExecutionRequest(xml=_XML))
    assert caught.value is primary
    assert len(reaped) == 1
    assert reaped[0].poll() is not None
