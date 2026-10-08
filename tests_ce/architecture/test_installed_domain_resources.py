"""Installed-wheel regression for namespace entrypoints and moved resources."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "datamimic_ce"
UV = shutil.which("uv")


def _run_installed(installation: Path, working_directory: Path, *, domain_data: Path | None = None) -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("DATAMIMIC_ROOT", None)
    environment.pop("DATAMIMIC_DOMAIN_DATA", None)
    environment["PYTHONPATH"] = str(installation)
    if domain_data is not None:
        environment["DATAMIMIC_DOMAIN_DATA"] = str(domain_data)
    script = """
import json
import sys
from importlib.metadata import distribution
from pathlib import Path

import datamimic_ce
import datamimic_ce.engine as engine
import datamimic_ce.interfaces as interfaces
import datamimic_ce.interfaces.cli as cli
import datamimic_ce.interfaces.mcp as mcp

assert "datamimic_ce.interfaces.cli._app" not in sys.modules
assert "datamimic_ce.interfaces.mcp.server" not in sys.modules
from datamimic_ce.interfaces.cli import app
from datamimic_ce.interfaces.cli._app import app as defined_app
from datamimic_ce.interfaces.cli.__main__ import main as cli_main
from datamimic_ce.interfaces.mcp import create_server, mount_mcp
from datamimic_ce.interfaces.mcp.cli import main as mcp_main
from datamimic_ce.interfaces.mcp.server import create_server as defined_server, mount_mcp as defined_mount
from datamimic_ce.interfaces.python.datamimic import DataMimic
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest
from datamimic_ce.interfaces.python.factory import DataMimicTestFactory
import datamimic_ce.engine.dsl.api as dsl_api
import datamimic_ce.engine.io.api as io_api
import datamimic_ce.engine.runtime.api as runtime_api
from datamimic_ce.resources.api import demo_root

assert app is defined_app and create_server is defined_server and mount_mcp is defined_mount
for cls, module in [(DataMimic, "datamimic"), (DataMimicTest, "data_mimic_test"), (DataMimicTestFactory, "factory")]:
    assert cls.__module__ == "datamimic_ce.interfaces.python." + module
entrypoints = {entry.name: entry for entry in distribution("datamimic_ce").entry_points}
assert entrypoints["datamimic"].load() is cli_main
assert entrypoints["datamimic-mcp"].load() is mcp_main
assert datamimic_ce.__file__ is not None
installed_root = Path(datamimic_ce.__file__).resolve().parent.parent
assert list(engine.__path__) == [str(installed_root / "datamimic_ce" / "engine")]
assert callable(dsl_api.DescriptorParser) and callable(io_api.Memstore) and callable(runtime_api.create_run_session)
from datamimic_ce.domains.domain_core.datasets.path import dataset_path
from datamimic_ce.domains.registry.schema import load_schema
from datamimic_ce.domains.shared.literal_generators.person.given_name_generator import GivenNameGenerator

dataset = dataset_path("common", "person", "givenName_male_US.csv")
result = {
    "package": str(Path(datamimic_ce.__file__).resolve()),
    "interfaces_path": str(Path(next(iter(interfaces.__path__))).resolve()),
    "interfaces_namespace": str(interfaces.__file__ is None),
    "engine_path": str(Path(next(iter(engine.__path__))).resolve()),
    "engine_namespace": str(engine.__file__ is None),
    "demo_resource": str(demo_root().joinpath("demo-ecommerce", "datamimic.xml").is_file()),
    "dataset": str(dataset.resolve()),
    "dataset_exists": str(dataset.is_file()),
    "name": GivenNameGenerator(dataset="US", gender="male").generate() if dataset.is_file() else "",
    "schema": type(load_schema("person", "request", "v1")).__name__,
}
for name, module in list(sys.modules.items()):
    if name == "datamimic_ce" or name.startswith("datamimic_ce."):
        if module.__file__ is not None:
            assert Path(module.__file__).resolve().is_relative_to(installed_root)
            assert Path(module.__spec__.origin).resolve() == Path(module.__file__).resolve()
        else:
            assert all(Path(path).resolve().is_relative_to(installed_root) for path in module.__path__)
print(json.dumps(result))
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=working_directory,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return json.loads(result.stdout)


def test_moved_domain_resources_work_from_an_installed_wheel(tmp_path: Path) -> None:
    wheel_directory = tmp_path / "wheel"
    installation = tmp_path / "installation"
    outside_checkout = tmp_path / "outside-checkout"
    wheel_directory.mkdir()
    outside_checkout.mkdir()
    assert UV, "the project wheel smoke test requires uv"

    subprocess.run(
        [UV, "build", "--out-dir", str(wheel_directory)],
        cwd=ROOT,
        check=True,
        timeout=120,
    )
    wheel = next(wheel_directory.glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        wheel_modules = {
            name.removeprefix("datamimic_ce/")
            for name in archive.namelist()
            if name.startswith("datamimic_ce/") and name.endswith(".py")
        }
        assert wheel_modules == {path.relative_to(PACKAGE).as_posix() for path in PACKAGE.rglob("*.py")}
        assert not any(name.startswith(("tests_ce/", "docs/", "test-artifacts/")) for name in archive.namelist())
    subprocess.run(
        [UV, "pip", "install", "--python", sys.executable, "--no-deps", "--target", str(installation), str(wheel)],
        check=True,
        timeout=120,
    )

    installed = _run_installed(installation, outside_checkout)
    assert Path(installed["package"]).is_relative_to(installation)
    assert not Path(installed["package"]).is_relative_to(ROOT)
    assert Path(installed["dataset"]).is_relative_to(installation)
    assert installed["dataset_exists"] == "True"
    assert installed["name"]
    assert installed["schema"] == "Draft7Validator"

    override = tmp_path / "override"
    override_file = override / "common" / "person" / "givenName_male_US.csv"
    override_file.parent.mkdir(parents=True)
    override_file.write_text("Override,1\n", encoding="utf-8")
    overridden = _run_installed(installation, outside_checkout, domain_data=override)
    assert Path(overridden["dataset"]) == override_file
    assert overridden["name"] == "Override"

    missing_override = tmp_path / "missing-override"
    missing = _run_installed(installation, outside_checkout, domain_data=missing_override)
    assert Path(missing["dataset"]) == missing_override / "common" / "person" / "givenName_male_US.csv"
    assert missing["dataset_exists"] == "False"
    assert not missing["name"]

    assert Path(installed["interfaces_path"]) == installation / "datamimic_ce" / "interfaces"
    assert installed["interfaces_namespace"] == str(not (PACKAGE / "interfaces" / "__init__.py").exists())
    assert Path(installed["engine_path"]) == installation / "datamimic_ce" / "engine"
    assert installed["engine_namespace"] == str(not (PACKAGE / "engine" / "__init__.py").exists())
    assert installed["demo_resource"] == "True"
    environment = dict(os.environ, PYTHONPATH=str(installation))
    for command in ["datamimic", "datamimic-mcp"]:
        result = subprocess.run(
            [str(installation / "bin" / command), "--help"],
            cwd=outside_checkout,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "Usage:" in result.stdout
