import copy
from pathlib import Path

from datamimic_ce.domains.api import RunSeed
from datamimic_ce.engine.dsl.model.setup.setup_model import SetupModel
from datamimic_ce.engine.dsl.statements.setup.setup_statement import SetupStatement
from datamimic_ce.engine.io.exporters.diagnostics.test_result_exporter import TestResultExporter
from datamimic_ce.engine.runtime.contexts.context import SetupContext
from datamimic_ce.engine.runtime.storage.global_increment import GlobalIncrementRegistry
from datamimic_ce.engine.runtime.storage.memstore_manager import MemstoreManager


def _context() -> SetupContext:
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
        properties={"nested": [1]},
        namespace={"nested": [1]},
        global_variables={"shared": [1]},
        generators={"cached": [1]},
        run_seed=RunSeed.create(7),
    )


def test_setup_context_deepcopy_shares_globals_but_resets_runtime_state() -> None:
    context = _context()
    original_rng = context.rng
    original_faker = context.seeded_faker
    context.global_increment_registry = GlobalIncrementRegistry()

    copied = copy.deepcopy(context)

    assert copied.global_variables is context.global_variables
    assert copied.properties == context.properties and copied.properties is not context.properties
    assert copied.namespace == context.namespace and copied.namespace is not context.namespace
    assert copied.generators == context.generators and copied.generators is not context.generators
    assert copied.run_seed is context.run_seed
    assert copied.rng is not original_rng
    assert copied.rng.getrandbits(64) == original_rng.getrandbits(64)
    assert copied.seeded_faker is not original_faker
    assert copied.global_increment_registry is None


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
