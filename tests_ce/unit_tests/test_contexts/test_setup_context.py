import ast
import copy
import pickle
import inspect
import textwrap
from pathlib import Path
from typing import get_type_hints
from unittest.mock import patch

import dill
import pytest

from datamimic_ce.domains.api import RunSeed
from datamimic_ce.engine.dsl.model.setup.include_model import IncludeModel
from datamimic_ce.engine.dsl.model.setup.memstore_model import MemstoreModel
from datamimic_ce.engine.dsl.model.setup.setup_model import SetupModel
from datamimic_ce.engine.dsl.statements.setup.include_statement import IncludeStatement
from datamimic_ce.engine.dsl.statements.setup.memstore_statement import MemstoreStatement
from datamimic_ce.engine.dsl.statements.setup.setup_statement import SetupStatement
from datamimic_ce.engine.io.api import Client, Exporter, Memstore, RegisteredClient
from datamimic_ce.engine.dsl.vocabulary.enums.dbms_enums import Dbms
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig
from datamimic_ce.engine.io.exporters.diagnostics.test_result_exporter import TestResultExporter
from datamimic_ce.engine.io.exporters import registry as exporter_registry
from datamimic_ce.engine.io.exporters import session as export_session_module
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.storage.global_increment import GlobalIncrementRegistry
from datamimic_ce.engine.runtime.storage.memstore_manager import MemstoreManager
from datamimic_ce.engine.runtime.tasks.setup.include_task import IncludeTask
from datamimic_ce.engine.runtime.tasks.setup.memstore_task import MemstoreTask
from datamimic_ce.engine.runtime.tasks.values.construction.converters import create_converter_list


def _context(
    clients: dict[str, RegisteredClient] | None = None,
    namespace: dict[str, object] | None = None,
    global_variables: dict[str, object] | None = None,
    properties: dict[str, object] | None = None,
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
        properties=properties,
        namespace={"nested": [1]} if namespace is None else namespace,
        global_variables={"shared": [1]} if global_variables is None else global_variables,
        generators={"cached": [1]},
        run_seed=RunSeed.create(7),
    )


def test_setup_context_deepcopy_shares_globals_but_resets_runtime_state() -> None:
    context = _context(properties={"nested": [1]})
    original_rng = context.rng
    original_faker = context.seeded_faker
    context.global_increment_registry = GlobalIncrementRegistry()

    copied = copy.deepcopy(context)

    assert copied.memstore_manager is context.memstore_manager
    assert copied.global_variables is context.global_variables
    assert copied.properties == context.properties and copied.properties is not context.properties
    assert copied.properties["nested"] is not context.properties["nested"]
    assert copied.namespace == context.namespace and copied.namespace is not context.namespace
    assert copied.generators == context.generators and copied.generators is not context.generators
    assert copied.run_seed is context.run_seed
    assert copied.rng is not original_rng
    assert copied.rng.getrandbits(64) == original_rng.getrandbits(64)
    assert copied.seeded_faker is not original_faker
    assert copied.global_increment_registry is None


def test_setup_context_deepcopy_preserves_shared_property_references_within_copy() -> None:
    shared: list[object] = []
    context = _context(properties={"first": shared, "second": shared})

    copied = copy.deepcopy(context)

    assert copied.properties is not context.properties
    assert copied.properties["first"] is copied.properties["second"]
    assert copied.properties["first"] is not shared


def test_setup_context_deepcopy_propagates_noncopyable_property_error() -> None:
    class NonCopyable:
        def __deepcopy__(self, memo: dict[int, object]) -> object:
            raise TypeError("cannot copy property value")

    value = NonCopyable()
    context = _context(properties={"value": value})

    with pytest.raises(TypeError, match="^cannot copy property value$"):
        copy.deepcopy(context)

    assert context.properties["value"] is value


def test_setup_context_properties_annotations_describe_mutable_object_mapping() -> None:
    native_properties = dict[str, str] | dict[str, object]
    assert get_type_hints(SetupContext.__init__).get("properties") == native_properties | None
    assert get_type_hints(SetupContext.properties.fget).get("return") == native_properties
    assert get_type_hints(SetupContext.properties.fset).get("value") == native_properties
    assert get_type_hints(SetupContext.properties.fset).get("return") is type(None)

    tree = ast.parse(textwrap.dedent(inspect.getsource(SetupContext.__init__)))
    property_assignment = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Attribute)
        and isinstance(node.target.value, ast.Name)
        and node.target.value.id == "self"
        and node.target.attr == "_properties"
    )
    assert ast.unparse(property_assignment.annotation) == "dict[str, str] | dict[str, object]"


@pytest.mark.parametrize("properties", [None, {}])
def test_setup_context_properties_default_or_supplied_empty_mapping(properties) -> None:
    context = _context(properties=properties)

    if properties is None:
        assert context.properties == {}
        assert context.properties is not _context(properties=None).properties
    else:
        assert context.properties is properties


def test_setup_context_properties_preserves_nonempty_and_replacement_identity() -> None:
    nested = [1, {"enabled": True}]
    supplied = {"quoting": 3, "nested": nested}
    context = _context(properties=supplied)

    assert context.properties is supplied
    assert context.properties["quoting"] == 3
    assert context.properties["nested"] is nested

    replacement = {"replacement": ["value"]}
    context.properties = replacement
    assert context.properties is replacement


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


def test_add_client_registers_lookup_and_script_namespace_identity() -> None:
    context = _context()
    client = Client()

    context.add_client("db", client)

    assert context.clients["db"] is client
    assert context.get_client_by_id("db") is client
    assert context.get_client_by_id("missing") is None
    assert context.evaluate_python_expression("db") is client
    assert context.eval_namespace("script_client = db")["script_client"] is client


def test_setup_context_deepcopy_preserves_client_alias_without_disposing_engine(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    client = RdbmsClient(
        RdbmsConnectionConfig(
            dbms=Dbms.SQLITE,
            host=None,
            port=None,
            user=None,
            password=None,
            database="context-copy",
            db_schema=None,
        ),
        task_id="context-test",
    )
    engine = client._create_engine()
    dispose_calls = []
    dispose = engine.dispose

    def track_dispose(*args, **kwargs):
        dispose_calls.append(True)
        return dispose(*args, **kwargs)

    monkeypatch.setattr(engine, "dispose", track_dispose)
    context = _context()
    context.add_client("db", client)

    copied = copy.deepcopy(context)

    assert dispose_calls == []
    assert client.engine is engine
    assert copied.clients["db"] is copied.namespace["db"] is client


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


def test_include_properties_merges_into_the_supplied_mapping_in_place(tmp_path: Path) -> None:
    (tmp_path / "included.properties").write_text("existing=replaced\nadded=value\n", encoding="utf-8")
    supplied = {"existing": "original", "quoting": 3, "nested": [1, {"key": "value"}]}
    context = _context(properties=supplied)
    context._descriptor_dir = tmp_path
    task = IncludeTask(IncludeStatement(IncludeModel(uri="included.properties")))

    task.execute(context)

    assert context.properties is supplied
    assert supplied == {
        "existing": "replaced",
        "added": "value",
        "quoting": 3,
        "nested": [1, {"key": "value"}],
    }


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
    assert get_type_hints(SetupContext.__init__).get("clients") == dict[str, RegisteredClient] | None
    assert get_type_hints(SetupContext.clients.fget).get("return") == dict[str, RegisteredClient]
    assert get_type_hints(SetupContext.clients.fset).get("value") == dict[str, RegisteredClient]
    assert get_type_hints(SetupContext.add_client).get("client") is RegisteredClient
    assert get_type_hints(SetupContext.add_client).get("return") is type(None)
    assert get_type_hints(SetupContext.get_client_by_id).get("return") == RegisteredClient | None
    deepcopy_clients_hints = get_type_hints(SetupContext._deepcopy_clients)
    assert deepcopy_clients_hints.get("memo") == dict[int, object]
    assert deepcopy_clients_hints.get("return") == dict[str, RegisteredClient]


def test_client_registry_copy_does_not_dispose_callers_and_preserves_shared_memo() -> None:
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

    copied = copy.deepcopy(context)

    assert events == ["copy:first", "copy:second"]
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


@pytest.mark.parametrize(
    ("constructor", "message"),
    [
        ("ScriptValue", "Converter 'ScriptValue' is not callable"),
        ("ScriptValue()", "Converter expression 'ScriptValue()' did not create a Converter"),
    ],
    ids=["without-parentheses", "with-parentheses"],
)
def test_scripted_class_and_instance_remain_native_and_non_converter_is_rejected(
    constructor: str, message: str
) -> None:
    context = _context()
    updated = context.eval_namespace(
        "class ScriptValue:\n"
        "    def __init__(self):\n"
        "        self.value = 42\n"
        "instance = ScriptValue()"
    )
    context.namespace.update(updated)

    dynamic_class = context.get_dynamic_class("ScriptValue")
    instance = context.namespace["instance"]
    assert dynamic_class is updated["ScriptValue"]
    assert instance is updated["instance"]
    assert instance.__class__ is dynamic_class
    assert context.evaluate_python_expression("instance.value") == 42
    with pytest.raises(TypeError) as raised:
        create_converter_list(context, constructor)
    assert str(raised.value) == message


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




def test_memstore_facade_manager_and_export_dispatch_share_canonical_classes() -> None:
    context = _context(namespace={})
    MemstoreTask(MemstoreStatement(MemstoreModel(id="mem"))).execute(context)
    store = context.memstore_manager.get_memstore("mem")

    assert context.namespace["mem"] is store
    assert type(store) is Memstore
    assert exporter_registry.Memstore is export_session_module.Memstore is Memstore
    assert exporter_registry.Exporter is export_session_module.Exporter is Exporter
    assert Memstore.__bases__ == (Exporter,)
    assert Memstore.__mro__ == (Memstore, Exporter, object)
    assert isinstance(store, Exporter)
    for codec in (pickle, dill):
        assert codec.loads(codec.dumps((Memstore, Exporter))) == (Memstore, Exporter)


def test_setup_context_memstore_deepcopy_preserves_existing_manager_namespace_split() -> None:
    context = _context(namespace={})
    MemstoreTask(MemstoreStatement(MemstoreModel(id="mem"))).execute(context)
    store = context.memstore_manager.get_memstore("mem")
    context.namespace["alias"] = store
    store.consume(("rows", [{"id": 1, "nested": []}]))

    copied = copy.deepcopy(context)

    assert copied.memstore_manager is context.memstore_manager
    assert copied.memstore_manager.get_memstore("mem") is store
    assert copied.namespace["mem"] is copied.namespace["alias"]
    assert copied.namespace["mem"] is not store
    copied.namespace["mem"].get_data_by_type("rows")[0]["nested"].append("copied")
    assert store.get_data_by_type("rows") == [{"id": 1, "nested": []}]

    restored = dill.loads(dill.dumps(copied))
    assert restored.memstore_manager is not copied.memstore_manager
    assert restored.namespace["mem"] is restored.namespace["alias"]
    assert restored.namespace["mem"] is not restored.memstore_manager.get_memstore("mem")
    assert type(restored.namespace["mem"]) is Memstore
    assert restored.namespace["mem"].get_data_by_type("rows") == [{"id": 1, "nested": ["copied"]}]
    assert restored.memstore_manager.get_memstore("mem").get_data_by_type("rows") == [{"id": 1, "nested": []}]


@pytest.mark.parametrize("codec", [pickle, dill], ids=["pickle", "dill"])
def test_registered_memstore_graph_serialization_preserves_internal_aliases(codec) -> None:
    context = _context(namespace={})
    MemstoreTask(MemstoreStatement(MemstoreModel(id="mem"))).execute(context)
    store = context.memstore_manager.get_memstore("mem")
    store.consume(("rows", [{"id": 1, "nested": []}]))
    graph = {"manager": context.memstore_manager, "namespace": context.namespace, "store": store}

    for restored in (copy.deepcopy(graph), codec.loads(codec.dumps(graph))):
        restored_store = restored["store"]
        assert restored_store is restored["namespace"]["mem"] is restored["manager"].get_memstore("mem")
        assert restored_store is not store
        assert type(restored_store) is Memstore
        restored_store.get_data_by_type("rows")[0]["nested"].append("copied")
        assert store.get_data_by_type("rows") == [{"id": 1, "nested": []}]


# These are locally produced, same-checkpoint trusted serializations. The graph
# round trip does not replace the actual SetupContext test or prove worker transport.
