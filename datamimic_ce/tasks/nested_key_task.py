# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import copy
import random

from datamimic_ce.constants.data_type_constants import DATA_TYPE_DICT, DATA_TYPE_LIST
from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.data_sources.data_source_util import DataSourceUtil
from datamimic_ce.logger import logger
from datamimic_ce.statements.nested_key_statement import NestedKeyStatement
from datamimic_ce.tasks.element_task import ElementTask
from datamimic_ce.tasks.task import Task
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil
from datamimic_ce.utils.file_util import FileUtil


class NestedKeyTask(Task):
    def __init__(
        self,
        ctx: SetupContext,
        statement: NestedKeyStatement,
        class_factory_util: BaseClassFactoryUtil,
    ):
        self._statement = statement
        self._default_value = statement.default_value
        self._descriptor_dir = ctx.root.descriptor_dir
        self._class_factory_util = class_factory_util
        self._sub_tasks: list | None = None
        self._converter_list = class_factory_util.get_task_util_cls().create_converter_list(ctx, statement.converter)

    @property
    def statement(self) -> NestedKeyStatement:
        return self._statement

    def execute(self, parent_context: Context) -> None:
        """
        Generate data for element "nestedKey"
        :param parent_context:
        :return:
        """
        task_util_cls = self._class_factory_util.get_task_util_cls()
        # Lazy creating sub_tasks of nestedkey_task for refreshing state of sub_tasks among nestedkey_tasks
        self._sub_tasks = [
            task_util_cls.get_task_by_statement(
                ctx=parent_context.root,
                stmt=child_stmt,
            )
            for child_stmt in self._statement.sub_statements
        ]

        # check condition to enable or disable element, default True
        condition = task_util_cls.evaluate_condition_value(
            ctx=parent_context,
            element_name=self._statement.name,
            value=self._statement.condition,
        )
        if isinstance(parent_context, GenIterContext):
            if condition:
                # If both source and script are None, create new nestedkey instead of loading data from file
                if self._statement.source is None and self._statement.script is None:
                    self._execute_generate(parent_context)
                else:
                    self._execute_iterate(parent_context)
            elif self._default_value is not None:
                # If condition false and default_value exist, assign default value to nestedKey
                default_value = parent_context.evaluate_python_expression(self._default_value)
                default_value = self._post_convert(default_value)
                parent_context.add_current_product_field(self._statement.name, default_value)

    def _lazy_init_sub_tasks(self, parent_context: GenIterContext, nestedkey_length: int):
        """
        Lazy creating sub_tasks of nestedkey_task for refreshing state of sub_tasks among nestedkey_tasks

        :return:
        """
        # Set pagination as length of list
        task_util_cls = self._class_factory_util.get_task_util_cls()
        self._sub_tasks = [
            task_util_cls.get_task_by_statement(
                ctx=parent_context.root,
                stmt=child_stmt,
                pagination=DataSourcePagination(skip=0, limit=nestedkey_length),
            )
            for child_stmt in self._statement.sub_statements
        ]

    def _execute_generate(self, parent_context: GenIterContext) -> None:
        """
        Create new data for nestedkey
        """
        nestedkey_type = self._statement.type
        value: dict | list
        if nestedkey_type == DATA_TYPE_LIST:
            nestedkey_len = self._determine_nestedkey_length(context=parent_context)
            value = []
            if nestedkey_len:
                self._lazy_init_sub_tasks(parent_context=parent_context, nestedkey_length=nestedkey_len)
                # Generate data for each nestedkey record
                for _ in range(nestedkey_len):
                    # Create sub-context for each list element creation
                    ctx = GenIterContext(parent_context, str(self._statement.name))
                    generated_value = self._try_execute_sub_tasks(ctx)
                    value.append(generated_value)
        elif nestedkey_type == DATA_TYPE_DICT:
            self._lazy_init_sub_tasks(parent_context=parent_context, nestedkey_length=1)
            # Create sub-context for nestedkey creation
            ctx = GenIterContext(parent_context, str(self._statement.name))
            value = self._try_execute_sub_tasks(ctx)
        else:
            # Load value from current product then assign to nestedkey if type is not defined,
            # this is used from enriching template data
            logger.debug(
                f"Type of nestedkey '{self._statement.name}' is not defined, load value from current "
                f"product/template instead and merge with additional configuration"
            )
            nestedkey_data = parent_context.current_product[self._statement.name]
            self._lazy_init_sub_tasks(parent_context=parent_context, nestedkey_length=len(nestedkey_data))
            ctx = GenIterContext(parent_context, str(self._statement.name))
            ctx.current_product = nestedkey_data
            value = self._try_execute_sub_tasks(ctx)

        # Add field "nestedKey" into current product
        parent_context.add_current_product_field(self._statement.name, value)

    def _execute_iterate(self, parent_context: GenIterContext) -> None:
        """
        Load data from file and modify then assign to nestedkey
        """
        if self._statement.script is not None:
            try:
                result = self._evaluate_value_from_script(parent_context)
            except Exception as e:
                if self._default_value is not None:
                    result = parent_context.evaluate_python_expression(self._default_value)
                    logger.debug(
                        f"Could not evaluate script of element '{self._statement.name}'. "
                        f"Default value '{self._default_value}'  will be used instead."
                    )
                else:
                    raise ValueError(f"Failed when execute script of element '{self._statement.name}'") from e
        elif self._statement.source:
            result = self._load_data_from_source(parent_context)
            is_random_distribution = self._statement.distribution in ("random", None)
            # Shuffle data if distribution is random
            if is_random_distribution:
                # Use task_id as seed for random distribution
                pass

                seed = parent_context.root.get_distribution_seed()
                result = DataSourceUtil.get_shuffled_data_with_cyclic(result, None, self._statement.cyclic, seed)
        else:
            raise ValueError(f"Cannot load original data for <nestedKey> '{self._statement.name}'")

        # Post convert value after executing sub-tasks
        if isinstance(result, list):
            result = list(map(lambda ele: self._post_convert(ele), result))
        elif isinstance(result, dict):
            result = self._post_convert(result)
        elif result is None:
            pass
        else:
            raise ValueError(
                f"Expect evaluated datatype of script '{self._statement.script}' (of element <{self._statement.name}>)"
                f" is 'list' or 'dict', but get invalid datatype: '{type(result)}'"
            )

        # Add field "nestedKey" into current product
        parent_context.add_current_product_field(self._statement.name, result)

    def _try_execute_sub_tasks(self, ctx: GenIterContext) -> dict:
        """
        Try to execute sub-tasks of nestedkey_task. Throw StopIteration error when any source reach the end
        :param ctx:
        :return:
        """
        attributes = {}
        # Try to execute sub_tasks
        if self._sub_tasks:
            for sub_task in self._sub_tasks:
                try:
                    if isinstance(sub_task, ElementTask):
                        attributes.update(sub_task.generate_xml_attribute(ctx))
                    else:
                        sub_task.execute(ctx)
                except StopIteration:
                    # Stop generating data if one of datasource reach the end
                    logger.info(
                        f"Data generator sub-task {sub_task.__class__.__name__} '{sub_task.statement.name}' "
                        f"has already reached the end"
                    )
                    break
        ctx.current_product = self._post_convert(ctx.current_product)
        return {**ctx.current_product, **attributes}

    def _evaluate_value_from_script(self, parent_context: GenIterContext) -> list | dict:
        """
        Evaluate data using script

        :param parent_context:
        :return:
        """
        value = parent_context.evaluate_python_expression(self._statement.script)
        result: dict | list
        if isinstance(value, list):
            result = self._modify_nestedkey_data_list(parent_context, value)
        elif isinstance(value, dict):
            result = self._modify_nestedkey_data_dict(parent_context, value)
        else:
            raise ValueError(
                f"Expect evaluated datatype of script '{self._statement.script}' is 'list' or 'dict', "
                f"but get invalid datatype: '{type(value)}'"
            )
        return result

    def _load_data_from_source(self, parent_context: Context) -> list | dict:
        """
        Load data from source

        :param parent_context:
        :return:
        """
        source_str = self._statement.source
        nestedkey_type = self._statement.type
        result: dict | list

        # Evaluate scripted source string
        source = (
            parent_context.evaluate_python_expression(source_str[1:-1])
            if source_str.startswith("{") and source_str.endswith("}")
            else source_str
        )
        if nestedkey_type == DATA_TYPE_LIST and isinstance(parent_context, GenIterContext):
            # Read data from source
            if source.endswith("csv"):
                separator = self._statement.separator or parent_context.root.default_separator
                list_value = FileUtil.read_csv_to_dict_list(
                    file_path=self._descriptor_dir / source, separator=separator
                )
            elif source.endswith("json"):
                list_value = FileUtil.read_json_to_dict_list(self._descriptor_dir / source)
            else:
                raise ValueError(f"Invalid source '{source}' of nestedkey '{self._statement.name}'")

            result = self._modify_nestedkey_data_list(parent_context, list_value)

        elif nestedkey_type == DATA_TYPE_DICT and isinstance(parent_context, GenIterContext):
            if source.endswith("json"):
                dict_value = FileUtil.read_json_to_dict(self._descriptor_dir / source)
                result = self._modify_nestedkey_data_dict(parent_context, dict_value)
            else:
                raise ValueError(f"Source of nestedkey having type as 'dict' does not support format {source}")

        # handle memstore source
        elif parent_context.root.memstore_manager.contain(source_str) and isinstance(parent_context, GenIterContext):
            list_value = parent_context.root.memstore_manager.get_memstore(source_str).get_data_by_type(
                self._statement.type, None, self._statement.cyclic
            )

            result = self._modify_nestedkey_data_list(parent_context, list_value)
        else:
            raise ValueError(
                f"Cannot load data from source '{self._statement.source}' of <nestedKey> '{self._statement.name}'"
            )

        # sourceScripted evaluate python expression
        source_scripted = (
            self._statement.source_script
            if self._statement.source_script is not None
            else bool(parent_context.root.default_source_scripted)
        )
        if source_scripted:
            from datamimic_ce.tasks.task_util import TaskUtil

            # Determine variable prefix and suffix
            ctx = parent_context.parent if isinstance(parent_context, GenIterContext) else parent_context
            while isinstance(ctx, GenIterContext):
                ctx = ctx.parent
            if isinstance(ctx, SetupContext):
                variable_prefix = self.statement.variable_prefix or ctx.default_variable_prefix
                variable_suffix = self.statement.variable_suffix or ctx.default_variable_suffix
            else:
                variable_prefix = self.statement.variable_prefix
                variable_suffix = self.statement.variable_suffix

            # Evaluate source_script
            result = TaskUtil.evaluate_file_script_template(parent_context, result, variable_prefix, variable_suffix)

        return result

    def _modify_nestedkey_data_dict(self, parent_context: GenIterContext, value: dict) -> dict:
        """
        Modify original dict data of nestedkey

        :param parent_context:
        :param value:
        :return:
        """
        self._lazy_init_sub_tasks(parent_context=parent_context, nestedkey_length=1)
        # Create sub-context for nestedkey creation
        ctx = GenIterContext(parent_context, str(self._statement.name))
        ctx.current_product = copy.copy(value)
        modified_value = self._try_execute_sub_tasks(ctx)
        return modified_value

    def _modify_nestedkey_data_list(self, parent_context: GenIterContext, value: list) -> list[dict]:
        """
        Modify original list data of nestedKey
        :param value:
        :return:
        """
        result = []

        # Determine len of nestedkey
        count = self._determine_nestedkey_length(context=parent_context)
        value_len = len(value)
        # https://gitlab.dwellerlab.com/rapiddweller/datamimic_ce/rd-lib-datamimic_ce/-/merge_requests/98#note_10678
        nestedkey_len = value_len if count is None else count if self._statement.cyclic else min(count, value_len)

        # Init original data of nestedkey
        iterate_value = DataSourceUtil.get_cyclic_data_list(
            data=value,
            pagination=DataSourcePagination(0, nestedkey_len),
            cyclic=self._statement.cyclic,
        )

        # Modify port data
        self._lazy_init_sub_tasks(parent_context=parent_context, nestedkey_length=nestedkey_len)
        # Modify each nestedkey of the data
        for idx in range(nestedkey_len):
            ctx = GenIterContext(parent_context, str(self._statement.name))
            ctx.current_product = iterate_value[idx]

            # Ensure current_product is a dictionary
            if not isinstance(ctx.current_product, dict):
                raise ValueError(
                    f"Expect current product of nestedkey '{self._statement.name}' is a dictionary, "
                    f"but get invalid datatype: '{type(ctx.current_product)}'"
                )

            modified_value = self._try_execute_sub_tasks(ctx)
            result.append(modified_value)

        return result

    def _determine_nestedkey_length(self, context: Context) -> int | None:
        """
        Determine nestedkey length based on count, minCount and maxCount

        :return:
        """
        count = self._statement.get_int_count(context)
        min_count = self._statement.min_count
        max_count = self._statement.max_count

        if count is not None:
            return count
        if count is None and min_count is None and max_count is None:
            return None

        if min_count is None:
            return random.randint(max(0, max_count - 5), max_count)
        elif max_count is None:
            return random.randint(min_count, min_count + 5)
        else:
            return random.randint(min_count, max_count)

    def _post_convert(self, value):
        """
        Post convert value after executing sub-tasks
        :param value:
        :return:
        """
        for converter in self._converter_list:
            value = converter.convert(value)
        return value
