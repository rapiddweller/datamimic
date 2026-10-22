"""Public CE identity and import boundaries after the explicit API migration."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from datamimic_ce.authoring import AuthoringApplication, create_authoring_application
from datamimic_ce.authoring.application.app import AuthoringApplication as InternalApplication
from datamimic_ce.authoring.bootstrap import create_authoring_application as InternalFactory
from datamimic_ce.authoring.domain.requests import AuthoringSchemaId, ReferenceRequest
from datamimic_ce.engine.dsl import api as dsl_api
from datamimic_ce.engine.dsl.api import TimeSeriesNamespace
from datamimic_ce.engine.dsl.model.generation.timeseries import TimeSeriesNamespace as InternalTimeSeriesNamespace
from datamimic_ce.engine.runtime.api import Context, DemographicContext, SetupContext
from datamimic_ce.engine.runtime.contexts.context import Context as InternalContext
from datamimic_ce.engine.runtime.contexts.context import SetupContext as InternalSetupContext
from datamimic_ce.engine.runtime.contexts.demographic_context import DemographicContext as InternalDemographicContext


def test_public_contract_exports_preserve_identity():
    assert AuthoringApplication is InternalApplication
    assert create_authoring_application is InternalFactory


def test_public_factory_supports_schema_and_reference_without_execution(tmp_path):
    app = create_authoring_application(workspace_root=tmp_path)
    schema = app.schema(AuthoringSchemaId.BUILD_REQUEST_V5)
    assert schema["properties"]["version"]["const"] == "5.0"
    assert app.reference(ReferenceRequest()).ok
    assert list(tmp_path.iterdir()) == []


def test_public_import_does_not_initialize_runtime_or_optional_transports():
    script = "import sys,json; import datamimic_ce.authoring; print(json.dumps([m for m in sys.modules if m.startswith(('datamimic_ce.engine.runtime','datamimic_ce.engine.io','datamimic_ce.interfaces.mcp','datamimic_ee'))]))"
    result = subprocess.run([sys.executable, "-c", script], cwd=Path(__file__).parents[3], check=True, capture_output=True, text=True)
    assert json.loads(result.stdout) == []


def test_legacy_authoring_modules_have_no_import_shim():
    for module in ("datamimic_ce.authoring.spec", "datamimic_ce.authoring.api", "datamimic_ce.authoring.application.compiler"):
        assert importlib.util.find_spec(module) is None


def test_runtime_and_dsl_api_export_types_by_identity() -> None:
    assert Context is InternalContext
    assert SetupContext is InternalSetupContext
    assert DemographicContext is InternalDemographicContext
    assert TimeSeriesNamespace is InternalTimeSeriesNamespace


def test_dsl_api_exports_time_series_namespace_by_identity() -> None:
    assert dsl_api.TimeSeriesNamespace is TimeSeriesNamespace
    assert "TimeSeriesNamespace" in dsl_api.__all__
