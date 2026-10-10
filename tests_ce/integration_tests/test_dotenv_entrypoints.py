"""Subprocess contracts for package imports and dotenv entrypoints."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_CONFIG_KEYS = (
    "DATAMIMIC_CONFIG",
    "DATAMIMIC_DOMAIN_DATA",
    "DATAMIMIC_MCP_API_KEY",
    "DATAMIMIC_MCP_HOST",
    "DATAMIMIC_MCP_PORT",
    "DATAMIMIC_ROOT",
    "DATAMIMIC_STRICT_DATASET",
    "DATAMIMIC_TEST_VALUE",
    "DATAMIMIC_IMPORT_DOTENV_SENTINEL",
    "RUNTIME_ENVIRONMENT",
)


def _environment(**overrides: str) -> dict[str, str]:
    environment = os.environ.copy()
    for key in _CONFIG_KEYS:
        environment.pop(key, None)
    environment["PYTHONPATH"] = str(ROOT)
    environment.update(overrides)
    return environment


def _run_python(directory: Path, source: str, **environment: str) -> str:
    result = subprocess.run(
        [sys.executable, "-c", source],
        cwd=directory,
        env=_environment(**environment),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _write_domain_catalog(root: Path, code: str) -> None:
    files = (
        "common/person/givenName_male_{code}.csv",
        "common/person/givenName_female_{code}.csv",
        "common/person/familyName_{code}.csv",
        "common/person/title_{code}.csv",
        "common/street/street_{code}.csv",
        "common/city/city_{code}.csv",
        "common/state/state_{code}.csv",
        "healthcare/medical/specialties_{code}.csv",
        "healthcare/medical/hospitals_{code}.csv",
        "healthcare/medical/medical_conditions_{code}.csv",
        "healthcare/medical/insurance_providers_{code}.csv",
    )
    for relative in files:
        path = root / relative.format(code=code)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("value,weight\nexample,1\n", encoding="utf-8")


def test_package_and_domain_imports_do_not_load_cwd_dotenv(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(
        "DATAMIMIC_DOMAIN_DATA=/dotenv/data\nDATAMIMIC_STRICT_DATASET=1\n",
        encoding="utf-8",
    )

    output = _run_python(
        tmp_path,
        """
import json, os
before = dict(os.environ)
import datamimic_ce
import datamimic_ce.domains.api
print(json.dumps({"unchanged": os.environ == before,
                  "domain_data": "DATAMIMIC_DOMAIN_DATA" in os.environ,
                  "strict_dataset": "DATAMIMIC_STRICT_DATASET" in os.environ}))
""",
    )

    assert json.loads(output) == {"unchanged": True, "domain_data": False, "strict_dataset": False}


def test_domains_honor_explicit_environment_without_package_bootstrap(tmp_path: Path) -> None:
    data = tmp_path / "domain-data"
    data.mkdir()
    output = _run_python(
        tmp_path,
        """
import json
from datamimic_ce.domains.domain_core.datasets.path import domain_data_root, is_strict_dataset_mode
print(json.dumps({"root": str(domain_data_root()), "strict": is_strict_dataset_mode()}))
""",
        DATAMIMIC_DOMAIN_DATA=str(data),
        DATAMIMIC_STRICT_DATASET="1",
    )

    assert json.loads(output) == {"root": str(data), "strict": True}


@pytest.mark.parametrize(
    ("process_value", "expected"),
    [(None, "from-dotenv"), ("from-process", "from-process")],
)
def test_cli_loads_startup_dotenv_without_overriding_process_environment(
    tmp_path: Path, process_value: str | None, expected: str
) -> None:
    (tmp_path / ".env").write_text("DATAMIMIC_CONFIG=from-dotenv\n", encoding="utf-8")
    environment = _environment(
        **({} if process_value is None else {"DATAMIMIC_CONFIG": process_value})
    )
    result = subprocess.run(
        [sys.executable, "-m", "datamimic_ce.interfaces.cli", "info"],
        cwd=tmp_path,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    assert expected in result.stdout


@pytest.mark.parametrize(
    ("process_values", "expected"),
    [({}, ("0.0.0.0", 8766, "dotenv-key")),
     ({"DATAMIMIC_MCP_HOST": "127.0.0.2", "DATAMIMIC_MCP_PORT": "8767", "DATAMIMIC_MCP_API_KEY": "process-key"},
      ("127.0.0.2", 8767, "process-key"))],
)
def test_mcp_uses_startup_dotenv_and_process_environment_wins(
    tmp_path: Path,
    process_values: dict[str, str],
    expected: tuple[str, int, str],
) -> None:
    (tmp_path / ".env").write_text(
        "DATAMIMIC_MCP_HOST=0.0.0.0\n"
        "DATAMIMIC_MCP_PORT=8766\n"
        "DATAMIMIC_MCP_API_KEY=dotenv-key\n",
        encoding="utf-8",
    )
    output = _run_python(
        tmp_path,
        """
import json
from datamimic_ce.interfaces.mcp import cli

captured = {}

def start_with_stubs():
    from datamimic_ce.interfaces.mcp import server
    server.create_server = lambda: object()
    server.build_sse_app = lambda current, api_key: captured.update(api_key=api_key) or object()
    cli.serve()

cli.app = start_with_stubs
cli.uvicorn.run = lambda app, host, port, log_level: captured.update(host=host, port=port)
cli.main()
print(json.dumps(captured))
""",
        **process_values,
    )

    assert json.loads(output.splitlines()[-1]) == {
        "host": expected[0],
        "port": expected[1],
        "api_key": expected[2],
    }


@pytest.mark.parametrize("entrypoint", ["cli", "mcp"])
@pytest.mark.parametrize("explicit_environment", [False, True])
def test_executable_loads_dotenv_before_domain_catalog_import(
    tmp_path: Path, entrypoint: str, explicit_environment: bool
) -> None:
    dotenv_root = tmp_path / "dotenv-data"
    _write_domain_catalog(dotenv_root, "ZZ")
    process_root = tmp_path / "process-data"
    if explicit_environment:
        _write_domain_catalog(process_root, "YY")
    (tmp_path / ".env").write_text(f"DATAMIMIC_DOMAIN_DATA={dotenv_root}\n", encoding="utf-8")
    expected_root = process_root if explicit_environment else dotenv_root
    expected_code = "YY" if explicit_environment else "ZZ"

    if entrypoint == "cli":
        source = """
import json, sys, typer
sys.argv = ["datamimic", "info"]
typer.Typer.__call__ = lambda self, *args, **kwargs: None
from datamimic_ce.interfaces.cli.__main__ import main
main()
assert "datamimic_ce.domains.healthcare.generators.patient_generator" in sys.modules
"""
    else:
        source = """
import json, sys
from datamimic_ce.interfaces.mcp import cli
assert "datamimic_ce.domains.healthcare.generators.patient_generator" not in sys.modules
assert "datamimic_ce.domains.shared.datasets.locales" not in sys.modules
cli.app = lambda: None
cli.main()
assert "datamimic_ce.domains.healthcare.generators.patient_generator" not in sys.modules
assert "datamimic_ce.domains.shared.datasets.locales" not in sys.modules
"""

    output = _run_python(
        tmp_path,
        source
        + """
from datamimic_ce.domains.healthcare.generators import patient_generator
from datamimic_ce.domains.shared.datasets import locales
print("OBS=" + json.dumps({
    "condition_dir": str(patient_generator._CONDITION_DATA_DIR),
    "patient_datasets": sorted(locales._PATIENT_DATASETS),
}))
""",
        **({"DATAMIMIC_DOMAIN_DATA": str(process_root)} if explicit_environment else {}),
    )
    observed_line = next(line for line in output.splitlines() if line.startswith("OBS="))

    assert json.loads(observed_line.removeprefix("OBS=")) == {
        "condition_dir": str(expected_root / "healthcare" / "medical"),
        "patient_datasets": [expected_code],
    }


def test_mcp_rejects_invalid_dotenv_port_before_server_setup(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("DATAMIMIC_MCP_PORT=invalid\n", encoding="utf-8")
    output = _run_python(
        tmp_path,
        """
import json
import typer
from datamimic_ce.interfaces.mcp import cli

events = []
def start_with_stub():
    from datamimic_ce.interfaces.mcp import server
    server.create_server = lambda: events.append("server")
    cli.serve()
cli.app = start_with_stub
try:
    cli.main()
except typer.BadParameter as exc:
    print(json.dumps({"error": str(exc), "events": events}))
""",
    )

    assert json.loads(output) == {"error": "DATAMIMIC_MCP_PORT must be an integer", "events": []}


@pytest.mark.parametrize(
    ("dotenv_value", "process_value", "expected"),
    [("development", None, "production"), ("production", "development", "development")],
)
def test_runtime_settings_ignore_cwd_dotenv_and_honor_explicit_environment(
    tmp_path: Path, dotenv_value: str, process_value: str | None, expected: str
) -> None:
    (tmp_path / ".env").write_text(
        f"RUNTIME_ENVIRONMENT={dotenv_value}\nDATAMIMIC_IMPORT_DOTENV_SENTINEL=loaded\n",
        encoding="utf-8",
    )
    output = _run_python(
        tmp_path,
        """
import json, os
import datamimic_ce.engine.runtime.api
from datamimic_ce.engine.runtime.lifecycle.config import get_settings
print(json.dumps({"environment": get_settings().RUNTIME_ENVIRONMENT,
                  "dotenv_loaded": "DATAMIMIC_IMPORT_DOTENV_SENTINEL" in os.environ}))
""",
        **({} if process_value is None else {"RUNTIME_ENVIRONMENT": process_value}),
    )

    assert json.loads(output) == {"environment": expected, "dotenv_loaded": False}


def test_seeded_descriptor_output_matches_under_same_explicit_environment(tmp_path: Path) -> None:
    descriptor = tmp_path / "seeded.xml"
    descriptor.write_text(
        '<setup rngSeed="7" multiprocessing="False">'
        '<generate name="rows" count="3" target="">'
        '<key name="environment_value" script="os.getenv(\'DATAMIMIC_TEST_VALUE\', \'missing\')" />'
        '</generate></setup>',
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text("DATAMIMIC_TEST_VALUE=from-dotenv\n", encoding="utf-8")
    source = f"""
import json
from pathlib import Path
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest
engine = DataMimicTest(Path({str(tmp_path)!r}), "seeded.xml", capture_test_result=True)
engine.test_with_timer()
print("RESULT=" + json.dumps(engine.capture_result(), sort_keys=True))
"""

    first = _run_python(tmp_path, source, DATAMIMIC_TEST_VALUE="explicit")
    second = _run_python(tmp_path, source, DATAMIMIC_TEST_VALUE="explicit")
    result_lines = [line.removeprefix("RESULT=") for line in (first, second) for line in line.splitlines()
                    if line.startswith("RESULT=")]

    assert len(result_lines) == 2
    assert result_lines[0] == result_lines[1]
    assert json.loads(result_lines[0]) == {
        "rows": [{"environment_value": "explicit"}] * 3,
    }
