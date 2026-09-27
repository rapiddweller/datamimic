# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from __future__ import annotations  # Enable forward declarations

import copy
import random
import re
import secrets
import types
from abc import ABC, abstractmethod
from pathlib import Path
from random import Random
from typing import Literal, TypedDict

from faker import Faker

from datamimic_ce.domains.api import (
    BaseLiteralGenerator,
    Converter,
    CustomConverter,
    RunSeed,
    derive_child_seed,
    spawn_rng,
)
from datamimic_ce.engine.dsl.api import ExportOperation, SetupStatement
from datamimic_ce.engine.io.api import Client, Exporter, TestResultExporter, dispose_client_engine
from datamimic_ce.engine.runtime.contexts.demographic_context import DemographicContext
from datamimic_ce.engine.runtime.contexts.expression_globals import NON_VALUE_TYPES, expression_globals
from datamimic_ce.engine.runtime.logging import logger
from datamimic_ce.engine.runtime.scripting.evaluation import evaluate_python
from datamimic_ce.engine.runtime.scripting.plugins import execute_script
from datamimic_ce.engine.runtime.storage.global_increment import GlobalIncrementRegistry
from datamimic_ce.engine.runtime.storage.memstore_manager import MemstoreManager
from datamimic_ce.randomness import RandomSource

# The number-one authoring trap: bare record-local names only resolve at the top level.
# Appended to undefined-name errors so the failure itself teaches the scope rule.
_SCOPE_GUIDANCE = (
    "a same-scope sibling resolves bare (or via this.) - check the name; "
    "an ANCESTOR scope's name needs parent./root., it does not resolve bare"
)


class Context(ABC):
    def __init__(self, root_context: SetupContext):  # noqa: F821
        self._root = root_context
        self._statement_start_times: dict[str, float] = {}

    @property
    def root(self) -> SetupContext:  # noqa: F821
        return self._root

    @property
    @abstractmethod
    def rng(self) -> RandomSource:
        """The rng for randomness driven by this context (Random or random module)."""

    @property
    def statement_start_times(self) -> dict[str, float]:
        return self._statement_start_times

    @statement_start_times.setter
    def statement_start_times(self, value: dict[str, float]) -> None:
        self._statement_start_times = value

    def evaluate_python_expression(self, expr: str, local_namespace: dict[str, object] | None = None) -> object:
        """
        Get reference from current variables and attributes
        :param local_namespace:
        :param expr:
        :return:
        """
        current_context = self
        # Init data_dict with local_namespace
        data_dict = {} if local_namespace is None else copy.deepcopy(local_namespace)

        # Update data_dict with root context's properties'
        if current_context.root.properties is not None:
            data_dict.update(current_context.root.properties)

        # Update data_dict with current context's variables and products
        content_tree = self.get_content_variables_products(current_context)
        data_dict.update(content_tree)

        # Evaluate python expression, use dict of products and variables as local namespace
        # Convert namespace dict to dotable dict
        for key, value in data_dict.items():
            if isinstance(value, dict):
                data_dict[key] = DotableDict(value)

        # Canonical scope aliases, mirroring DATAMIMIC EE (bound only when not already a user name):
        #  - `this`: the current content scope, so `this.field` == bare `field` (essential in nested
        #    scopes where a bare sibling name is wrapped under the scope name and does not resolve).
        #  - `parent`: the immediate parent generate/nestedKey scope.
        #  - `root`: the full merged content tree from the outermost scope down (root.<field> / root.<name>.<field>).
        if "this" not in data_dict:
            data_dict["this"] = DotableDict(self._current_scope())
        if "parent" not in data_dict:
            parent_scope = self._parent_scope()
            if parent_scope:
                data_dict["parent"] = DotableDict(parent_scope)
        if "root" not in data_dict:
            data_dict["root"] = DotableDict(dict(content_tree))

        is_seeded = self.root.is_seeded
        eval_globals = expression_globals(
            is_seeded=is_seeded,
            rng=self.rng if is_seeded else None,
            seeded_faker_supplier=lambda: self.root.seeded_faker,
        )
        try:
            result = evaluate_python(expr, eval_globals, data_dict)

            if isinstance(result, DotableDict):
                return result.to_dict()
            elif isinstance(result, list):
                return [ele.to_dict() if isinstance(ele, DotableDict) else ele for ele in result]
            # check result is not function, class or module
            elif callable(result) or isinstance(result, types.ModuleType):
                raise ValueError(f"'{expr}' is an callable function, not a valid type (string, integer, float,...)")
            elif type(result) in NON_VALUE_TYPES:
                raise ValueError(
                    f"'{expr}' is {type(result).__name__} function, not a valid type (string, integer, float,...)"
                )
            else:
                return result
        except NameError as e:
            # Same exception TYPE as before (ValueError) — only the message improves:
            # name the missing identifier and teach the scope rule.
            missing = e.name if e.name is not None else str(e)
            raise ValueError(
                f"Failed while evaluate '{expr}': name '{missing}' is not defined in this scope; {_SCOPE_GUIDANCE}"
            ) from e
        except AttributeError as e:
            # DotableDict raises this for a missing field on this./parent./root. (str(e)
            # already names it: "Cannot find attribute 'x'"); native ones carry e.name.
            missing_attr = f"missing attribute '{e.name}'" if e.name is not None else str(e)
            raise ValueError(f"Failed while evaluate '{expr}': {missing_attr}; {_SCOPE_GUIDANCE}") from e
        except KeyError as e:
            missing_key = e.args[0] if e.args else str(e)
            raise ValueError(f"Failed while evaluate '{expr}': missing key {missing_key!r}") from e
        except TypeError as e:
            raise ValueError(f"Failed while evaluate '{expr}': '{expr}' have undefined item or wrong structure") from e
        except SyntaxError as e:
            # special case with expr have ':' (example xml tag: 'gc:CodeList')
            if ":" in expr:
                # encode ':' character
                colon_replacement = "__"
                expr = expr.replace(r"\:", "__")

                def process_after_dot(match):
                    # After the first dot, replace all : with __
                    part_after_dot = match.group(1)
                    return "." + re.sub(r"[:]", "__", part_after_dot)

                # Find the first dot and apply the transformation
                expr = re.sub(r"\.(.*)", process_after_dot, expr)

                def recursion_data_dict(recursion_dict):
                    updated_dict = {}
                    for recursion_key, recursion_value in recursion_dict.items():
                        if isinstance(recursion_value, dict):
                            recursion_value = recursion_data_dict(recursion_value)
                        if isinstance(recursion_value, DotableDict):
                            recursion_value = DotableDict(recursion_data_dict(recursion_value.to_dict()))
                        updated_dict[recursion_key.replace(":", colon_replacement)] = recursion_value
                    return updated_dict

                updated_data_dict = recursion_data_dict(data_dict)
                try:
                    result = evaluate_python(expr, eval_globals, updated_data_dict)
                    if isinstance(result, DotableDict):
                        return result.to_dict()
                    elif isinstance(result, list):
                        return [ele.to_dict() if isinstance(ele, DotableDict) else ele for ele in result]
                    # check result is not function, class or module
                    elif callable(result) or isinstance(result, types.ModuleType):
                        raise ValueError(
                            f"'{expr}' is an callable function, not a valid type (string, integer, float,...)"
                        )
                    elif type(result) in NON_VALUE_TYPES:
                        raise ValueError(
                            f"'{expr}' is {type(result).__name__} "
                            f"function, not a valid type (string, integer, float,...)"
                        )
                    else:
                        return result
                except Exception as err:
                    # decode ':' character
                    expr = expr.replace(colon_replacement, ":")
                    raise ValueError(
                        f"Evaluation error for expression '{expr}': "
                        "The expression may contain undefined items, improper structure, "
                        "or case-sensitive issues (e.g., using 'true' instead of 'True'). "
                        "Please double-check that all parameters and type notations are correct and supported."
                    ) from err
            else:
                raise ValueError(
                    f"Evaluation error for expression '{expr}': "
                    "The expression may contain undefined elements, formatting errors, "
                    "or unsupported parameter names. Ensure that boolean values and all parameter names "
                    "(e.g., 'True' vs 'true') adhere to the required formats."
                ) from e
        except Exception as e:
            #  Keep error reporting consistent; avoid extra stdout noise from traceback.print_exc()
            raise ValueError(f"Failed while evaluate '{expr}': {str(e)}") from e

    def _current_scope(self) -> dict[str, object]:
        """The current content scope for the ``this`` alias: ``this.field`` resolves to the same value as
        bare ``field``. In a generate/iterate that is the record's variables + products (products win on a
        name clash); at setup level it is the setup namespace + global variables."""
        if self is self.root:
            return {**self.root.namespace, **self.root.global_variables}
        return self.scope_content()

    def _parent_scope(self) -> dict[str, object]:
        """The immediate parent scope for the ``parent`` alias: the parent generate/nestedKey's
        variables + products. Empty when there is no enclosing generate scope (top-level = setup parent)."""
        if self is self.root:
            return {}
        parent = self.parent
        if parent is not None and parent is not parent.root:
            return parent.scope_content()
        return {}

    @property
    def parent(self) -> Context | None:
        return None

    @property
    def scope_name(self) -> str:
        return ""

    def scope_content(self) -> dict[str, object]:
        return {}

    @staticmethod
    def get_content_variables_products(current_context: Context) -> dict[str, object]:
        data_dict: dict[str, object] = {}
        # SetupContext evaluate script
        if current_context is current_context.root:
            # Add current variable & product of outermost context
            data_dict = {
                **current_context.root.namespace,
                **current_context.root.global_variables,
                **data_dict,
            }
        # GenIterContext evaluate script
        else:
            # Nested wrapping tree: each scope holds its child scope under the child's name, so a
            # qualified path like `orders.line_items.product.field` resolves; the outermost scope's
            # own vars land at the top level and the setup namespace/globals merge in.
            self_context = current_context
            self_is_outermost = False
            while current_context is not current_context.root:
                parent_context = current_context.parent
                scope_content = current_context.scope_content()
                if parent_context is None or parent_context is parent_context.root:
                    data_dict = {
                        **current_context.root.namespace,
                        **current_context.root.global_variables,
                        **scope_content,
                        **data_dict,
                    }
                    self_is_outermost = current_context is self_context
                    break
                data_dict = {
                    current_context.scope_name: {**scope_content, **data_dict}
                }
                current_context = parent_context
            # The scope evaluating THIS script also resolves its own variables/products by bare
            # name, not only nested under its own scope name (mirrors what `this.` already exposes -
            # a sibling <variable> feeding a <key> script in the same nested scope). Self fills in
            # names an ancestor doesn't already provide bare; an ancestor's own bare name always
            # wins on a clash (`**data_dict` last), so a script combining an ancestor's and its own
            # same-named variable (e.g. `id + simple_user.id`, a real fixture in this repo) keeps
            # resolving bare `id` to the ancestor's, exactly as before this change.
            if not self_is_outermost and self_context is not self_context.root:
                data_dict = {**self_context.scope_content(), **data_dict}

        return data_dict


class DotableDict:
    """
    Dotable presentation of dict
    """

    def __init__(self, dictionary: dict[str, object]):
        self._dictionary = dictionary

    def __getattr__(self, name: str) -> object:
        if name in self._dictionary:
            item = self._dictionary[name]
            if isinstance(item, dict):
                return DotableDict(item)
            elif isinstance(item, list):
                return [DotableDict(x) if isinstance(x, dict) else x for x in item]
            else:
                return item
        else:
            raise AttributeError(f"Cannot find attribute '{name}'")

    def get(self, name: str) -> object:
        return self.__getattr__(name)

    def to_dict(self) -> dict[str, object]:
        """
        Convert DotableDict to dict
        :return:
        """
        return self._dictionary

    def keys(self):
        return self._dictionary.keys()

class TaskExporters(TypedDict):
    page_count: int
    with_operation: list[tuple[Exporter, ExportOperation]]
    without_operation: list[Exporter]


class SetupContext(Context):
    """
    Root context, saving clients and data source length info
    """

    def __init__(
        self,
        memstore_manager: MemstoreManager,
        task_id: str,
        test_mode: bool,
        test_result_exporter: TestResultExporter,
        default_separator: str,
        default_locale: str,
        default_dataset: str,
        use_mp: bool | None,
        descriptor_dir: Path,
        num_process: int | None,
        default_variable_prefix: str,
        default_variable_suffix: str,
        default_line_separator: str | None,
        clients: dict | None = None,
        data_source_len: dict | None = None,
        properties: dict | None = None,
        namespace: dict | None = None,
        global_variables: dict | None = None,
        generators: dict | None = None,
        default_source_scripted: bool | None = None,
        report_logging: bool = True,
        demographic_context: DemographicContext | None = None,
        run_seed: RunSeed | None = None,
        domain_identifier_registry: dict[tuple[str, str], set[str]] | None = None,
        runtime_environment: Literal["development", "production"] = "production",
        ray_debug: bool = False,
    ):
        # SetupContext is always its root_context
        super().__init__(self)
        self._descriptor_dir = descriptor_dir
        self._clients = {} if clients is None else clients
        self._data_source_len = {} if data_source_len is None else data_source_len
        # Per-statement distribution seed, computed once and reused across a statement's pages so
        # paginated sub-task selection (random / cumulated / unique) stays globally consistent.
        self._distribution_seed_cache: dict[str | None, int] = {}
        self._properties = {} if properties is None else properties
        self._memstore_manager = memstore_manager
        self._namespace: dict[str, object] = {} if namespace is None else namespace
        self._accept_unknown_simple_types = True
        self._default_one_to_one = None
        self._default_imports = None
        self._max_count = 1000
        self._validate = False
        self._default_error_handler = None
        self._default_separator = default_separator or ","
        self._default_locale: str = default_locale or "en_US"
        self._default_dataset = default_dataset
        self._default_null = None
        self._default_script = "py"
        self._default_batch_size = 1
        self._default_line_separator = default_line_separator or "\n"
        self._default_encoding = "utf-8"
        self._use_mp = use_mp  # IMPORTANT: do not set default bool value to use_mp for config propagation
        self._task_id = task_id
        self._test_mode = test_mode
        self._test_result_exporter = test_result_exporter
        self._generators = generators or {}
        self._global_variables = {} if global_variables is None else global_variables
        self._num_process = num_process
        self._process_id: int | None = None
        self.global_increment_registry: GlobalIncrementRegistry | None = None
        self._domain_identifier_registry = {} if domain_identifier_registry is None else domain_identifier_registry
        self._default_variable_prefix = default_variable_prefix
        self._default_variable_suffix = default_variable_suffix
        # IMPORTANT: do not set default bool value to default_source_scripted for config propagation
        self._default_source_scripted = default_source_scripted
        self._report_logging = report_logging
        self._task_exporters: dict[str, TaskExporters] = {}
        self._serialized_generators: bytes | None = None
        self._demographic_context = demographic_context
        self._run_seed = run_seed if run_seed is not None else RunSeed.create(None)
        self.runtime_environment = runtime_environment
        self.ray_debug = ray_debug
        # Generator stream root: variables/keys without their own seed fork a reproducible child RNG from it.
        self._root_rng: Random | None = Random(self._run_seed.value) if self._run_seed.seeded else None
        # Cached call-time rng — populated lazily on first ``.rng`` access.
        self._call_rng: RandomSource | None = None
        self._seeded_faker: Faker | None = None

    def derive_seeded_rng(self) -> Random | None:
        """Fork a reproducible child RNG from the model-wide root seed.

        Returns ``None`` when no ``<setup rngSeed>`` was given, so the caller stays
        unseeded (wall-clock random).
        """
        return spawn_rng(self._root_rng) if self._root_rng is not None else None

    @property
    def run_seed(self) -> RunSeed:
        return self._run_seed

    @property
    def is_seeded(self) -> bool:
        """True when a model-wide <setup rngSeed> was given (determinism is expected)."""
        return self._run_seed.seeded

    @property
    def rng(self) -> RandomSource:
        """Cached call-time rng. Mirrors ``GenIterContext.rng`` so ``ctx.rng``
        works whether ``ctx`` is a SetupContext or a GenIterContext."""
        if self._call_rng is None:
            derived = self.derive_seeded_rng()
            self._call_rng = derived if derived is not None else random
        return self._call_rng

    @property
    def seeded_faker(self) -> Faker:
        """The Faker behind ``fake`` in this run's seeded script expressions; one per run keeps runs
        sharing a Python process from reseeding each other's instance."""
        if self._seeded_faker is None:
            self._seeded_faker = Faker()
        return self._seeded_faker

    def __deepcopy__(self, memo):
        """
        Select which attributes should be deepcopy
        :param memo:
        :return:
        """
        for _key, value in self._clients.items():
            dispose_client_engine(value)

        # Create a new instance of SetupContext with the copied attributes
        return SetupContext(
            task_id=self._task_id,
            memstore_manager=self._memstore_manager,
            use_mp=copy.deepcopy(self._use_mp, memo),
            clients=self._deepcopy_clients(memo),
            data_source_len=copy.deepcopy(self._data_source_len, memo),
            properties=copy.deepcopy(self._properties, memo),
            namespace=self._deepcopy_namespace(memo),
            test_mode=self._test_mode,
            descriptor_dir=self._descriptor_dir,
            test_result_exporter=self._test_result_exporter,
            default_separator=self._default_separator,
            default_dataset=self._default_dataset,
            default_locale=self._default_locale,
            global_variables=self.global_variables,
            generators=copy.deepcopy(self._generators, memo),
            num_process=copy.deepcopy(self._num_process, memo),
            default_variable_prefix=self._default_variable_prefix,
            default_variable_suffix=self._default_variable_suffix,
            default_line_separator=copy.deepcopy(self._default_line_separator, memo),
            default_source_scripted=self._default_source_scripted,
            report_logging=copy.deepcopy(self._report_logging),
            demographic_context=copy.deepcopy(self._demographic_context, memo),
            run_seed=self._run_seed,
            domain_identifier_registry=copy.deepcopy(self._domain_identifier_registry, memo),
            runtime_environment=self.runtime_environment,
            ray_debug=self.ray_debug,
        )

    @property
    def domain_identifier_registry(self) -> dict[tuple[str, str], set[str]]:
        return self._domain_identifier_registry

    def _deepcopy_clients(self, memo):
        """
        Deepcopy clients attribute, excluding non-pickleable objects.
        :param memo:
        :return:
        """
        copied_clients = {}
        for key, value in self._clients.items():
            try:
                copied_clients[key] = copy.deepcopy(value, memo)
            except TypeError as e:
                logger.warning(f"Cannot deepcopy client '{key}': {e}")
                copied_clients[key] = value  # Use the original object if deepcopy fails
        return copied_clients

    def _deepcopy_namespace(self, memo):
        """
        Deepcopy namespace attribute, excluding non-pickleable objects.
        :param memo:
        :return:
        """
        copied_namespace = {}
        for key, value in self._namespace.items():
            try:
                copied_namespace[key] = copy.deepcopy(value, memo)
            except TypeError as e:
                if self._use_mp:
                    logger.error(
                        "You are using multiprocessing, this means global imports are not supported "
                        "in your python script, please remove global imports and try again or alternatively "
                        "switch back to single process mode."
                    )
                    raise Exception("Global imports are not supported in multiprocessing mode.") from e
                logger.debug(f"Cannot deepcopy namespace item '{key}': {e}. Use the original object")
                copied_namespace[key] = value  # Use the original object if deepcopy fails
        return copied_namespace

    def eval_namespace(self, content: str) -> dict[str, object]:
        """
        Evaluate a given code content in a controlled namespace and update the dynamic classes.

        :param content: str, Python code to be executed.
        :return: dict, updated fields in the namespace.
        """
        # Prepare the namespace outside the lock
        initial_ns = dict(self._namespace)

        # Add Generator and Converter to the namespace for evaluation
        ns = {
            "Generator": BaseLiteralGenerator,
            "Converter": Converter,
            "CustomConverter": CustomConverter,
        }
        initial_ns.update(ns)

        try:
            # Execute the code and update the namespace
            execute_script(content, initial_ns)
        except Exception as e:
            logger.error(f"Error executing content: {e}")
            raise

        # Identify updated fields and remove functions from the namespace
        updated_fields: dict[str, object] = {}
        for key, value in initial_ns.items():
            if (
                not key.startswith("__")
                and not key.endswith("__")
                and (key not in self._namespace or self._namespace[key] != initial_ns[key])
            ):
                updated_fields[key] = value

        # Logging for debugging
        logger.debug(f"Updated namespace with fields: {updated_fields.keys()}")

        return updated_fields

    def get_dynamic_class(self, class_name: str) -> object | None:
        """
        Get dynamic class from namespace by class name is mostly for the usecase of
        dynamic generator and converter creation.
        :param class_name: for example: "CustomIntegerGenerator"
        :return: class object from namespace
        """
        return self._namespace.get(class_name)

    def update_with_stmt(self, stmt: SetupStatement):
        """
        Update new created setup_context with its own setup_stmt (propagate parent context props to sub context)
        :param stmt:
        :return:
        """
        if stmt.use_mp is not None:
            self.use_mp = stmt.use_mp
        if stmt.default_separator is not None:
            self.default_separator = stmt.default_separator
        if stmt.default_locale is not None:
            self.default_locale = stmt.default_locale
        if stmt.default_dataset is not None:
            self.default_dataset = stmt.default_dataset
        if stmt.num_process is not None:
            self.num_process = stmt.num_process
        if stmt.default_line_separator is not None:
            self._default_line_separator = stmt.default_line_separator
        if stmt.default_source_scripted is not None:
            self._default_source_scripted = stmt.default_source_scripted
        if stmt.report_logging is not None:
            self.report_logging = stmt.report_logging
        if stmt.default_variable_prefix is not None:
            self.default_variable_prefix = stmt.default_variable_prefix
        if stmt.default_variable_suffix is not None:
            self.default_variable_suffix = stmt.default_variable_suffix

    @property
    def demographic_context(self) -> DemographicContext | None:
        return self._demographic_context

    def set_demographic_context(self, context: DemographicContext) -> None:
        # Keep demographics explicit on the root context instead of mutable module globals.
        self._demographic_context = context

    @property
    def clients(self) -> dict:
        return self._clients

    @clients.setter
    def clients(self, value) -> None:
        self._clients = value

    @property
    def data_source_len(self):
        return self._data_source_len

    @property
    def properties(self):
        return self._properties

    @properties.setter
    def properties(self, value):
        self._properties = value

    @property
    def memstore_manager(self):
        return self._memstore_manager

    @property
    def namespace(self):
        return self._namespace

    @namespace.setter
    def namespace(self, value):
        self._namespace = value

    @property
    def namespace_functions(self) -> bytes | None:
        return self._namespace_functions

    @namespace_functions.setter
    def namespace_functions(self, value: bytes | None) -> None:
        self._namespace_functions = value

    @property
    def serialized_generators(self) -> bytes | None:
        return self._serialized_generators

    @serialized_generators.setter
    def serialized_generators(self, value: bytes | None) -> None:
        self._serialized_generators = value

    @property
    def use_mp(self) -> bool | None:
        return self._use_mp

    @use_mp.setter
    def use_mp(self, value):
        self._use_mp = value

    @property
    def task_id(self) -> str:
        return self._task_id

    @property
    def test_mode(self) -> bool:
        return self._test_mode

    @property
    def test_result_exporter(self) -> TestResultExporter:
        return self._test_result_exporter

    @property
    def descriptor_dir(self) -> Path:
        return self._descriptor_dir

    @property
    def task_exporters(self) -> dict[str, TaskExporters]:
        return self._task_exporters

    @task_exporters.setter
    def task_exporters(self, value: dict[str, TaskExporters]) -> None:
        self._task_exporters = value

    @property
    def default_separator(self) -> str:
        return self._default_separator

    @default_separator.setter
    def default_separator(self, value):
        self._default_separator = value

    @property
    def default_locale(self) -> str:
        return self._default_locale

    @default_locale.setter
    def default_locale(self, value):
        self._default_locale = value

    @property
    def default_dataset(self) -> str:
        return self._default_dataset

    @default_dataset.setter
    def default_dataset(self, value):
        self._default_dataset = value

    @property
    def global_variables(self) -> dict:
        return self._global_variables

    @property
    def generators(self) -> dict:
        return self._generators

    @generators.setter
    def generators(self, value) -> None:
        self._generators = value

    @property
    def num_process(self) -> int | None:
        return self._num_process

    @num_process.setter
    def num_process(self, value) -> None:
        self._num_process = value

    @property
    def process_id(self) -> int | None:
        """Worker id when the run is split across multiple processes; ``None`` otherwise."""
        return self._process_id

    @process_id.setter
    def process_id(self, value: int | None) -> None:
        self._process_id = value

    @property
    def default_variable_prefix(self) -> str:
        return self._default_variable_prefix

    @default_variable_prefix.setter
    def default_variable_prefix(self, value) -> None:
        self._default_variable_prefix = value

    @property
    def default_variable_suffix(self) -> str:
        return self._default_variable_suffix

    @default_variable_suffix.setter
    def default_variable_suffix(self, value) -> None:
        self._default_variable_suffix = value

    @property
    def default_line_separator(self) -> str:
        return self._default_line_separator

    @property
    def default_source_scripted(self) -> bool | None:
        return self._default_source_scripted

    @property
    def report_logging(self) -> bool:
        return self._report_logging

    @report_logging.setter
    def report_logging(self, value) -> None:
        self._report_logging = value

    @property
    def default_encoding(self) -> str:
        return self._default_encoding

    def add_client(self, client_id: str, client: Client):
        """
        Add client info to context
        :param client_id:
        :param client:
        :return:
        """
        self._clients[client_id] = client
        # Also bind by id into the script namespace (migration parity: <execute>/<variable script=>
        # can reference a declared <database>/<mongodb> id directly, e.g. `db.something()`) - both
        # eval_namespace (copies self._namespace wholesale) and evaluate_python_expression's scope
        # building read from this same dict, so this covers both script-evaluation paths regardless
        # of statement order.
        self._namespace[client_id] = client

    def get_client_by_id(self, client_id: str):
        """
        Get client using id defined in descriptor file
        :param client_id:
        :return:
        """
        return self._clients.get(client_id)

    def stable_distribution_seed(self, key: str | None) -> int:
        """A distribution seed that stays constant across a statement's pages and workers (``key`` is the
        statement full_name, unique per statement). A sub-task is rebuilt per page, so a fresh seed per call
        would break paginated random / cumulated / unique selection. Seeded runs draw it once from the root
        stream and cache it; unseeded runs key it from the run seed."""
        if not self._run_seed.seeded:
            return self._run_seed.int_for(f"distribution|{key}")
        if key not in self._distribution_seed_cache:
            self._distribution_seed_cache[key] = self.get_distribution_seed()
        return self._distribution_seed_cache[key]

    def get_distribution_seed(self) -> int:
        """A fresh seed for source shuffling (``distribution="random"``): drawn from the root stream when
        seeded, so a seeded read replays; random otherwise (the privacy-maximized default)."""
        if self._root_rng is None:
            return secrets.randbits(63)
        return derive_child_seed(self._root_rng)
