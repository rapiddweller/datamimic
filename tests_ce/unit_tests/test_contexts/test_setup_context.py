import copy
from pathlib import Path
from typing import get_type_hints
from unittest.mock import patch

import pytest

from datamimic_ce.domains.api import RunSeed
from datamimic_ce.engine.dsl.model.setup.setup_model import SetupModel
from datamimic_ce.engine.dsl.statements.setup.setup_statement import SetupStatement
from datamimic_ce.engine.io.api import Client
from datamimic_ce.engine.io.exporters.diagnostics.test_result_exporter import TestResultExporter
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.storage.global_increment import GlobalIncrementRegistry
from datamimic_ce.engine.runtime.storage.memstore_manager import MemstoreManager


def _context(
    clients: dict[str, Client] | None = None,
    namespace: dict[str, object] | None = None,
    global_variables: dict[str, object] | None = None,
) -> SetupContext:
    return SetupContext(
        memstore_manager=MemstoreManager(),
        task_id="context-test",
        test_mode=True,
        test_result_exporter=TestResultExporter(),
        default_separator="|",
        default_locale="en",
        default_dataset="US",
        use_mp=False,
        descriptor_dir=Path("."),
        num_process=1,
        default_variable_prefix="__",
        default_variable_suffix="__",
        default_line_separator="\n",
        clients=clients,
        properties={"nested": [1]},
        namespace={"nested": [1]} if namespace is None else namespace,
        global_variables={"shared": [1]} if global_variables is None else global_variables,
        generators={"cached": [1]},
        run_seed=RunSeed.create(7),
    )


def test_setup_context_deepcopy_shares_globals_but_resets_runtime_state() -> None:
    context = _context()
    original_rng = context.rng
    original_faker = context.seeded_faker
    context.global_increment_registry = GlobalIncrementRegistry()

    copied = copy.deepcopy(context)

    assert copied.memstore_manager is context.memstore_manager
    assert copied.global_variables is context.global_variables
    assert copied.properties == context.properties and copied.properties is not context.properties
    assert copied.namespace == context.namespace and copied.namespace is not context.namespace
    assert copied.generators == context.generators and copied.generators is not context.generators
    assert copied.run_seed is context.run_seed
    assert copied.rng is not original_rng
    assert copied.rng.getrandbits(64) == original_rng.getrandbits(64)
    assert copied.seeded_faker is not original_faker
    assert copied.global_increment_registry is None


def test_setup_context_deepcopy_isolates_domain_identifier_state() -> None:
    context = _context()
    registry = context.domain_identifier_registry
    assert registry.claim("TinyEntity", "id", "IDA", "ID[A-C]{1}") == "IDA"

    copied = copy.deepcopy(context)
    copied_registry = copied.domain_identifier_registry

    assert copied_registry is not registry
    assert copied_registry.claim("TinyEntity", "id", "IDA", "ID[A-C]{1}") == "IDB"
    assert copied_registry.claim("TinyEntity", "id", "IDA", "ID[A-C]{1}") == "IDC"
    assert registry.claim("TinyEntity", "id", "IDA", "ID[A-C]{1}") == "IDB"


def test_include_setup_merge_overrides_declared_defaults_but_preserves_run_seed() -> None:
    context = _context()
    statement = SetupStatement(
        SetupModel(
            multiprocessing=True,
            defaultSeparator=",",
            defaultLocale="de_DE",
            defaultDataset="DE",
            numProcess=3,
            defaultLineSeparator="\\r\\n",
            defaultSourceScripted=True,
            reportLogging=False,
            defaultVariablePrefix="${",
            defaultVariableSuffix="}",
            rngSeed=99,
        )
    )

    context.update_with_stmt(statement)

    assert context.use_mp is True
    assert context.default_separator == ","
    assert context.default_locale == "de_DE"
    assert context.default_dataset == "DE"
    assert context.num_process == 3
    assert context.default_line_separator == "\r\n"
    assert context.default_source_scripted is True
    assert context.report_logging is False
    assert context.default_variable_prefix == "${"
    assert context.default_variable_suffix == "}"
    assert context.run_seed.value == 7


def test_include_setup_merge_preserves_scalars_when_statement_values_are_none() -> None:
    context = _context()

    context.update_with_stmt(SetupStatement(SetupModel()))

    assert context.use_mp is False
    assert context.num_process == 1
    assert context.default_variable_prefix == "__"
    assert context.default_variable_suffix == "__"
    assert context.report_logging is True


def test_client_registry_keeps_mapping_and_client_identity() -> None:
    client = Client()
    supplied = {"db": client}
    context = _context(clients=supplied)

    assert context.clients is supplied
    assert context.get_client_by_id("db") is client
    assert context.get_client_by_id("missing") is None

    replacement = {"other": client}
    context.clients = replacement
    assert context.clients is replacement

    context.add_client("other", Client())
    replacement_client = context.get_client_by_id("other")
    assert replacement["other"] is replacement_client
    assert context._namespace["other"] is replacement_client
    assert context.get_client_by_id("missing") is None


def test_client_registry_annotations_describe_client_mapping() -> None:
    assert get_type_hints(SetupContext.__init__).get("clients") == dict[str, Client] | None
    assert get_type_hints(SetupContext.clients.fget).get("return") == dict[str, Client]
    assert get_type_hints(SetupContext.clients.fset).get("value") == dict[str, Client]
    assert get_type_hints(SetupContext.add_client).get("client") is Client
    assert get_type_hints(SetupContext.add_client).get("return") is type(None)
    assert get_type_hints(SetupContext.get_client_by_id).get("return") == Client | None
    deepcopy_clients_hints = get_type_hints(SetupContext._deepcopy_clients)
    assert deepcopy_clients_hints.get("memo") == dict[int, object]
    assert deepcopy_clients_hints.get("return") == dict[str, Client]


def test_client_registry_disposes_before_copy_and_preserves_shared_memo() -> None:
    events: list[str] = []

    class CopyableClient(Client):
        def __init__(self, name: str):
            self.name = name

        def __deepcopy__(self, memo):
            events.append(f"copy:{self.name}")
            return CopyableClient(self.name)

    context = _context()
    first = CopyableClient("first")
    second = CopyableClient("second")
    context.add_client("db-first", first)
    context.add_client("db-second", second)

    def dispose(value):
        if isinstance(value, CopyableClient):
            events.append(f"dispose:{value.name}")

    with patch(
        "datamimic_ce.engine.runtime.contexts.context.dispose_client_engine",
        side_effect=dispose,
    ):
        copied = copy.deepcopy(context)

    assert events == ["dispose:first", "dispose:second", "copy:first", "copy:second"]
    assert copied.clients["db-first"] is copied._namespace["db-first"]
    assert copied.clients["db-second"] is copied._namespace["db-second"]
    assert copied.clients["db-first"] is not first
    assert copied.clients["db-second"] is not second


def test_client_registry_keeps_original_when_deepcopy_raises_type_error() -> None:
    class NonCopyableClient(Client):
        def __deepcopy__(self, memo):
            raise TypeError("cannot copy client")

    context = _context()
    client = NonCopyableClient()
    context.add_client("db", client)

    copied = copy.deepcopy(context)

    assert copied.clients["db"] is client
    assert copied._namespace["db"] is client


def test_client_registry_propagates_non_type_error_from_deepcopy() -> None:
    error = ValueError("invalid client state")

    class InvalidClient(Client):
        def __deepcopy__(self, memo):
            raise error

    context = _context(clients={"db": InvalidClient()})

    with pytest.raises(ValueError) as raised:
        copy.deepcopy(context)

    assert raised.value is error


def test_setup_context_namespace_preserves_supplied_and_replacement_mapping_identity() -> None:
    supplied = {"value": object()}
    context = _context(namespace=supplied)

    assert context.namespace is supplied

    replacement = {"other": object()}
    context.namespace = replacement

    assert context.namespace is replacement


def test_setup_context_preserves_identity_of_supplied_empty_maps() -> None:
    namespace: dict[str, object] = {}
    global_variables: dict[str, object] = {}
    context = _context(namespace=namespace, global_variables=global_variables)

    assert context.namespace is namespace
    assert context.global_variables is global_variables


def test_setup_context_namespace_copies_arbitrary_objects_and_classes() -> None:
    class DynamicValue:
        def __init__(self, value: int) -> None:
            self.value = value

    value = DynamicValue(7)
    context = _context(namespace={"value": value, "type": DynamicValue})

    copied = copy.deepcopy(context)

    assert isinstance(copied.namespace["value"], DynamicValue)
    assert copied.namespace["value"].value == 7
    assert copied.namespace["type"] is DynamicValue


def test_setup_context_namespace_copy_preserves_aliases() -> None:
    shared = [1]
    context = _context(namespace={"first": shared, "second": shared})

    copied = copy.deepcopy(context)

    assert copied.namespace["first"] is copied.namespace["second"]
    assert copied.namespace["first"] is not shared


def test_namespace_type_error_falls_back_to_original_in_single_process_mode() -> None:
    class NonCopyable:
        def __deepcopy__(self, memo: dict[int, object]) -> object:
            raise TypeError("cannot copy namespace value")

    value = NonCopyable()
    context = _context(namespace={"value": value})

    copied = copy.deepcopy(context)

    assert copied.namespace["value"] is value


def test_namespace_type_error_in_multiprocessing_preserves_cause() -> None:
    class NonCopyable:
        def __deepcopy__(self, memo: dict[int, object]) -> object:
            raise TypeError("cannot copy namespace value")

    context = _context(namespace={"value": NonCopyable()})
    context.use_mp = True

    with pytest.raises(Exception, match="Global imports are not supported in multiprocessing mode.") as raised:
        copy.deepcopy(context)

    assert isinstance(raised.value.__cause__, TypeError)
    assert str(raised.value.__cause__) == "cannot copy namespace value"


def test_namespace_deepcopy_propagates_non_type_error() -> None:
    error = ValueError("invalid namespace state")

    class InvalidValue:
        def __deepcopy__(self, memo: dict[int, object]) -> object:
            raise error

    context = _context(namespace={"value": InvalidValue()})

    with pytest.raises(ValueError) as raised:
        copy.deepcopy(context)

    assert raised.value is error


def test_setup_context_state_annotations_describe_dynamic_namespace_and_copy_contract() -> None:
    init_hints = get_type_hints(SetupContext.__init__)
    assert init_hints.get("namespace") == dict[str, object] | None
    assert init_hints.get("global_variables") == dict[str, object] | None
    assert init_hints.get("return") is type(None)
    assert get_type_hints(SetupContext.namespace.fget).get("return") == dict[str, object]
    assert get_type_hints(SetupContext.namespace.fset).get("value") == dict[str, object]
    assert get_type_hints(SetupContext.namespace.fset).get("return") is type(None)
    assert get_type_hints(SetupContext.global_variables.fget).get("return") == dict[str, object]
    assert get_type_hints(SetupContext.memstore_manager.fget).get("return") is MemstoreManager
    assert get_type_hints(SetupContext.update_with_stmt).get("return") is type(None)
    deepcopy_hints = get_type_hints(SetupContext.__deepcopy__)
    assert deepcopy_hints.get("memo") == dict[int, object]
    assert deepcopy_hints.get("return") is SetupContext
    namespace_hints = get_type_hints(SetupContext._deepcopy_namespace)
    assert namespace_hints.get("memo") == dict[int, object]
    assert namespace_hints.get("return") == dict[str, object]
