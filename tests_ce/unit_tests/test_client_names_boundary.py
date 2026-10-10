from collections.abc import Iterable
from inspect import Parameter, signature
from typing import get_type_hints

from datamimic_ce.engine.io.clients.client import ClientNames, RegisteredClient
from datamimic_ce.engine.io.exporters.core.exporter_context import ExporterContext


def test_client_names_protocol_describes_the_exporter_boundary() -> None:
    assert ClientNames._is_protocol
    contains_parameters = signature(ClientNames.__contains__).parameters
    assert contains_parameters["client_id"].kind is Parameter.POSITIONAL_ONLY
    assert get_type_hints(ClientNames.__contains__) == {"client_id": str, "return": bool}
    assert get_type_hints(ClientNames.keys) == {"return": Iterable[str]}
    assert get_type_hints(ExporterContext.clients.fget) == {"return": ClientNames}
    assert get_type_hints(ExporterContext.get_client_by_id) == {
        "client_id": str,
        "return": RegisteredClient | None,
    }
