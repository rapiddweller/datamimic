# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import copy
import uuid
from pathlib import Path
from typing import Any

from datamimic_ce.clients.database_client import Client
from datamimic_ce.contexts.context import Context
from datamimic_ce.converter.converter import Converter
from datamimic_ce.converter.custom_converter import CustomConverter
from datamimic_ce.exporters.test_result_exporter import TestResultExporter
from datamimic_ce.generators.generator import Generator
from datamimic_ce.logger import logger
from datamimic_ce.product_storage.memstore_manager import MemstoreManager
from datamimic_ce.statements.setup_statement import SetupStatement
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class SetupContext(Context):
    """
    Root context, saving clients and data source length info
    """

    def __init__(
        self,
        class_factory_util: BaseClassFactoryUtil,
        memstore_manager: MemstoreManager,
        task_id: str,
        test_mode: bool,
        test_result_exporter: TestResultExporter | None,
        default_separator: str,
        default_locale: str,
        default_dataset: str,
        use_mp: bool | None,
        descriptor_dir: Path,
        num_process: int | None,
        default_variable_prefix: str,
        default_variable_suffix: str,
        default_line_separator: str | None,
        current_seed: int | None = None,
        clients: dict | None = None,
        data_source_len: dict | None = None,
        properties: dict | None = None,
        namespace: dict | None = None,
        global_variables: dict | None = None,
        generators: dict | None = None,
        default_source_scripted: bool | None = None,
        report_logging: bool = True,
    ):
        # SetupContext is always its root_context
        super().__init__(self)
        self._class_factory_util = class_factory_util
        self._descriptor_dir = descriptor_dir
        self._clients = {} if clients is None else clients
        self._data_source_len = {} if data_source_len is None else data_source_len
        self._properties = {} if properties is None else properties
        self._memstore_manager = memstore_manager
        self._namespace = {} if namespace is None else namespace
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
        self._default_variable_prefix = default_variable_prefix
        self._default_variable_suffix = default_variable_suffix
        # IMPORTANT: do not set default bool value to default_source_scripted for config propagation
        self._default_source_scripted = default_source_scripted
        self._report_logging = report_logging
        self._current_seed = current_seed
        self._task_exporters: dict[str, dict[str, Any]] = {}

    def __deepcopy__(self, memo):
        """
        Select which attributes should be deepcopy
        :param memo:
        :return:
        """
        # Close RDBMS engine
        from datamimic_ce.clients.rdbms_client import RdbmsClient

        for _key, value in self._clients.items():
            if isinstance(value, RdbmsClient) and value.engine is not None:
                value.engine.dispose()
                value.engine = None

        # Create a new instance of SetupContext with the copied attributes
        return SetupContext(
            class_factory_util=self._class_factory_util,
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
            generators=copy.deepcopy(self._generators),
            num_process=copy.deepcopy(self._num_process, memo),
            default_variable_prefix=self._default_variable_prefix,
            default_variable_suffix=self._default_variable_suffix,
            default_line_separator=copy.deepcopy(self._default_line_separator, memo),
            default_source_scripted=self._default_source_scripted,
            report_logging=copy.deepcopy(self._report_logging),
            current_seed=self._current_seed,
        )

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

    def eval_namespace(self, content):
        """
        Evaluate a given code content in a controlled namespace and update the dynamic classes.

        :param content: str, Python code to be executed.
        :return: dict, updated fields in the namespace.
        """
        # Prepare the namespace outside the lock
        initial_ns = dict(self._namespace)

        # Add Generator and Converter to the namespace for evaluation
        ns = {
            "Generator": Generator,
            "Converter": Converter,
            "CustomConverter": CustomConverter,
        }
        initial_ns.update(ns)

        try:
            # Execute the code and update the namespace
            exec(content, initial_ns)
        except Exception as e:
            logger.error(f"Error executing content: {e}")
            raise

        # Identify updated fields and remove functions from the namespace
        updated_fields = {}
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

    def get_dynamic_class(self, class_name: str):
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
        property_key = {name for name, value in vars(stmt.__class__).items() if isinstance(value, property)}
        for key in property_key:
            value = getattr(stmt, key)
            # Ignore not-defined props in parent context
            if value is not None:
                setattr(self, key, value)

    @property
    def class_factory_util(self):
        return self._class_factory_util

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
    def namespace_functions(self):
        return self._namespace_functions

    @namespace_functions.setter
    def namespace_functions(self, value):
        self._namespace_functions = value

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
    def test_result_exporter(self) -> TestResultExporter | None:
        return self._test_result_exporter

    @property
    def descriptor_dir(self) -> Path:
        return self._descriptor_dir

    @property
    def task_exporters(self) -> dict[str, dict[str, Any]]:
        return self._task_exporters

    @task_exporters.setter
    def task_exporters(self, value: dict[str, dict[str, Any]]) -> None:
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
    def default_encoding(self):
        return self._default_encoding

    def add_client(self, client_id: str, client: Client):
        """
        Add client info to context
        :param client_id:
        :param client:
        :return:
        """
        self._clients[client_id] = client

    def get_client_by_id(self, client_id: str):
        """
        Get client using id defined in descriptor file
        :param client_id:
        :return:
        """
        return self._clients.get(client_id)

    def get_distribution_seed(self) -> int:
        """
        Get distribution seed from task_id.
        Always return new seed on each call.
        :return:
        """
        # Return new seed on each call
        if self._current_seed is not None:
            self._current_seed += 1
        # If init seed is not set, calculate seed from task_id
        else:
            try:
                # Try to convert UUID task into int seed
                self._current_seed = uuid.UUID(self._task_id).int % 1000
            except ValueError as err:
                # If task_id is not a valid UUID, hash the string
                logger.warning(f"Invalid task_id '{self._task_id}': {err}")
                self._current_seed = hash(self._task_id) % 1000

        return self._current_seed
