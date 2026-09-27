"""Installed-wheel regression for moved domain resources."""

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
from pathlib import Path

import datamimic_ce
from datamimic_ce.domains.domain_core.datasets.path import dataset_path
from datamimic_ce.domains.registry.schema import load_schema
from datamimic_ce.domains.shared.literal_generators.person.given_name_generator import GivenNameGenerator

dataset = dataset_path("common", "person", "givenName_male_US.csv")
result = {
    "package": str(Path(datamimic_ce.__file__).resolve()),
    "dataset": str(dataset.resolve()),
    "dataset_exists": str(dataset.is_file()),
    "name": GivenNameGenerator(dataset="US", gender="male").generate() if dataset.is_file() else "",
    "schema": type(load_schema("person", "request", "v1")).__name__,
}
print(json.dumps(result))
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=working_directory,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
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
