# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import re
from typing import Any

from datamimic_ce.clients.mongodb_client import MongoDBClient
from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.converter.append_converter import AppendConverter
from datamimic_ce.converter.converter import Converter
from datamimic_ce.converter.cut_length_converter import CutLengthConverter
from datamimic_ce.converter.date2timestamp_converter import Date2TimestampConverter
from datamimic_ce.converter.date_format_converter import DateFormatConverter
from datamimic_ce.converter.hash_converter import HashConverter
from datamimic_ce.converter.java_hash_converter import JavaHashConverter
from datamimic_ce.converter.lower_case_converter import LowerCaseConverter
from datamimic_ce.converter.mask_converter import MaskConverter
from datamimic_ce.converter.middle_mask_converter import MiddleMaskConverter
from datamimic_ce.converter.remove_none_or_empty_element_converter import RemoveNoneOrEmptyElementConverter
from datamimic_ce.converter.timestamp2date_converter import Timestamp2DateConverter
from datamimic_ce.converter.upper_case_converter import UpperCaseConverter
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.enums.converter_enums import ConverterEnum
from datamimic_ce.exporters.csv_exporter import CSVExporter
from datamimic_ce.exporters.exporter_state_manager import ExporterStateManager
from datamimic_ce.exporters.json_exporter import JsonExporter
from datamimic_ce.exporters.memstore import Memstore
from datamimic_ce.exporters.mongodb_exporter import MongoDBExporter
from datamimic_ce.exporters.txt_exporter import TXTExporter
from datamimic_ce.exporters.xml_exporter import XMLExporter
from datamimic_ce.logger import logger
from datamimic_ce.statements.array_statement import ArrayStatement
from datamimic_ce.statements.condition_statement import ConditionStatement
from datamimic_ce.statements.database_statement import DatabaseStatement
from datamimic_ce.statements.echo_statement import EchoStatement
from datamimic_ce.statements.element_statement import ElementStatement
from datamimic_ce.statements.else_if_statement import ElseIfStatement
from datamimic_ce.statements.else_statement import ElseStatement
from datamimic_ce.statements.execute_statement import ExecuteStatement
from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.statements.generator_statement import GeneratorStatement
from datamimic_ce.statements.if_statement import IfStatement
from datamimic_ce.statements.include_statement import IncludeStatement
from datamimic_ce.statements.item_statement import ItemStatement
from datamimic_ce.statements.key_statement import KeyStatement
from datamimic_ce.statements.list_statement import ListStatement
from datamimic_ce.statements.memstore_statement import MemstoreStatement
from datamimic_ce.statements.mongodb_statement import MongoDBStatement
from datamimic_ce.statements.nested_key_statement import NestedKeyStatement
from datamimic_ce.statements.reference_statement import ReferenceStatement
from datamimic_ce.statements.rule_statement import RuleStatement
from datamimic_ce.statements.source_constraints_statement import ConstraintsStatement
from datamimic_ce.statements.statement import Statement
from datamimic_ce.statements.variable_statement import VariableStatement
from datamimic_ce.tasks.array_task import ArrayTask
from datamimic_ce.tasks.condition_task import ConditionTask
from datamimic_ce.tasks.database_task import DatabaseTask
from datamimic_ce.tasks.echo_task import EchoTask
from datamimic_ce.tasks.element_task import ElementTask
from datamimic_ce.tasks.else_if_task import ElseIfTask
from datamimic_ce.tasks.else_task import ElseTask
from datamimic_ce.tasks.execute_task import ExecuteTask
from datamimic_ce.tasks.generate_task import (
    GenerateTask,
)
from datamimic_ce.tasks.generator_task import GeneratorTask
from datamimic_ce.tasks.if_task import IfTask
from datamimic_ce.tasks.include_task import IncludeTask
from datamimic_ce.tasks.item_task import ItemTask
from datamimic_ce.tasks.key_task import KeyTask
from datamimic_ce.tasks.list_task import ListTask
from datamimic_ce.tasks.memstore_task import MemstoreTask
from datamimic_ce.tasks.mongodb_task import MongoDBTask
from datamimic_ce.tasks.nested_key_task import NestedKeyTask
from datamimic_ce.tasks.reference_task import ReferenceTask
from datamimic_ce.tasks.rule_task import RuleTask
from datamimic_ce.tasks.source_constraints_task import ConstraintsTask
from datamimic_ce.tasks.task import Task
from datamimic_ce.utils.object_util import ObjectUtil


class TaskUtil:
    @staticmethod
    def get_task_by_statement(
        ctx: SetupContext,
        stmt: Statement,
        pagination: DataSourcePagination | None = None,
    ) -> Task:
        class_factory_util = ctx.class_factory_util
        if isinstance(stmt, GenerateStatement):
            return GenerateTask(stmt, class_factory_util)
        elif isinstance(stmt, MongoDBStatement):
            return MongoDBTask(stmt)
        elif isinstance(stmt, DatabaseStatement):
            return DatabaseTask(stmt)
        elif isinstance(stmt, IncludeStatement):
            return IncludeTask(stmt)
        elif isinstance(stmt, MemstoreStatement):
            return MemstoreTask(stmt)
        elif isinstance(stmt, ExecuteStatement):
            return ExecuteTask(stmt)
        elif isinstance(stmt, KeyStatement):
            return KeyTask(ctx, stmt, pagination)
        elif isinstance(stmt, VariableStatement):
            from datamimic_ce.tasks.variable_task import VariableTask

            return VariableTask(ctx, stmt, pagination)
        elif isinstance(stmt, NestedKeyStatement):
            return NestedKeyTask(ctx, stmt, class_factory_util)
        elif isinstance(stmt, ArrayStatement):
            return ArrayTask(ctx, stmt)
        elif isinstance(stmt, ReferenceStatement):
            return ReferenceTask(stmt, pagination)
        elif isinstance(stmt, ListStatement):
            return ListTask(ctx=ctx, statement=stmt, class_factory_util=class_factory_util)
        elif isinstance(stmt, ItemStatement):
            return ItemTask(ctx, stmt, class_factory_util)
        elif isinstance(stmt, IfStatement):
            return IfTask(stmt, class_factory_util)
        elif isinstance(stmt, ConditionStatement):
            return ConditionTask(stmt, class_factory_util)
        elif isinstance(stmt, ElseIfStatement):
            return ElseIfTask(stmt, class_factory_util)
        elif isinstance(stmt, ElseStatement):
            return ElseTask(stmt, class_factory_util)
        elif isinstance(stmt, EchoStatement):
            return EchoTask(stmt)
        elif isinstance(stmt, ElementStatement):
            return ElementTask(ctx, stmt)
        elif isinstance(stmt, GeneratorStatement):
            return GeneratorTask(stmt)
        elif isinstance(stmt, ConstraintsStatement):
            return ConstraintsTask(stmt)
        elif isinstance(stmt, RuleStatement):
            return RuleTask(stmt)
        else:
            raise ValueError(f"Cannot created task for statement {stmt.__class__.__name__}")

    @staticmethod
    def evaluate_file_script_template(ctx: Context, datas: Any, prefix: str, suffix: str) -> dict | list:
        """
        Check value in csv or json file that contain python expression
        then evaluate variables and functions
        e.g. '{1+3}' -> 4
        """
        if isinstance(datas, dict):
            dict_result = {}
            for key, json_value in datas.items():
                if isinstance(json_value, dict | list):
                    value = TaskUtil.evaluate_file_script_template(ctx, json_value, prefix, suffix)
                elif isinstance(json_value, str):
                    value = TaskUtil._evaluate_script_value(ctx, json_value, prefix, suffix)
                else:
                    value = json_value
                dict_result.update({key: value})
            return dict_result
        elif isinstance(datas, list):
            list_result: list[Any] = []
            for value in datas:
                if isinstance(value, list):
                    list_result.extend(TaskUtil.evaluate_file_script_template(ctx, value, prefix, suffix))
                elif isinstance(value, dict):
                    list_result.append(TaskUtil.evaluate_file_script_template(ctx, value, prefix, suffix))
                elif isinstance(value, str):
                    list_result.append(TaskUtil._evaluate_script_value(ctx, value, prefix, suffix))
                else:
                    list_result.append(value)
            return list_result
        elif isinstance(datas, str):
            return TaskUtil._evaluate_script_value(ctx, datas, prefix, suffix)
        else:
            return datas

    @staticmethod
    def _evaluate_script_value(ctx: Context, data: str, prefix: str, suffix: str):
        """
        Evaluate python expression in data
        Python expression contain inside curly brackets
        e.g. '{1+3}'
        """
        try:
            if data is None or data.strip() == "":
                return data

            # Check if string is whole source script, e.g. {random_age(20,40)}
            is_whole_source_script = data[0] == "{" and data[-1] == "}"
            if is_whole_source_script:
                match = re.search(r"^{(.*)}$", data)
                return ctx.evaluate_python_expression(match.group(1)) if match is not None else None

            return TaskUtil.evaluate_variable_concat_prefix_suffix(ctx, data, prefix, suffix)

        except Exception as e:
            # logger.error(f"Error evaluating script '{data}': {e}")
            raise e

    @staticmethod
    def evaluate_condition_value(ctx: Context, element_name: str, value: str | None) -> bool:
        """
        Evaluate value in 'condition' property
        Value must be a boolean expression
        Use HTML entities name for comparison operators:
        """
        # Evaluate value of "condition"
        condition = ctx.evaluate_python_expression(value) if value else True
        # verify condition value syntax
        if isinstance(condition, bool):
            return condition
        else:
            raise ValueError(
                f"Evaluated value of condition script '{value}' in element '{element_name}' is not valid boolean value"
            )

    @staticmethod
    def create_converter_list(context: Context, converter_str: str | None) -> list[Converter]:
        """
        Create converter instance from converter_string
        :param context:
        :param converter_str:
        :return:
        """
        return (
            []
            if converter_str is None or converter_str == ""
            else list(
                map(
                    lambda ele: ObjectUtil.create_instance_from_constructor_str(
                        context=context,
                        constructor_str=ele.strip(),
                        class_dict={
                            ConverterEnum.LowerCase.value: LowerCaseConverter,
                            ConverterEnum.UpperCase.value: UpperCaseConverter,
                            ConverterEnum.DateFormat.value: DateFormatConverter,
                            ConverterEnum.Mask.value: MaskConverter,
                            ConverterEnum.MiddleMask.value: MiddleMaskConverter,
                            ConverterEnum.CutLength.value: CutLengthConverter,
                            ConverterEnum.Append.value: AppendConverter,
                            ConverterEnum.Hash.value: HashConverter,
                            ConverterEnum.JavaHash.value: JavaHashConverter,
                            ConverterEnum.Timestamp2Date.value: Timestamp2DateConverter,
                            ConverterEnum.Date2Timestamp.value: Date2TimestampConverter,
                            ConverterEnum.RemoveNoneOrEmptyElement.value: RemoveNoneOrEmptyElementConverter,
                        },
                    ),
                    converter_str.split(";"),
                )
            )
        )

    @staticmethod
    def evaluate_variable_concat_prefix_suffix(context: Context, expr: str, prefix: str, suffix: str) -> str:
        """
        Evaluate expression data, replace dynamic variables have prefix and suffix with value
        :param context:
        :param expr:
        :param prefix:
        :param suffix:
        :return:
        """
        # Check if string contain dynamic variable syntax, e.g. '__my_name__ is __my_age__ years old'
        # count group matching dynamic variable syntax
        pattern = rf"{re.escape(prefix)}([^{re.escape(prefix)}]\S*?){re.escape(suffix)}"
        matches = re.findall(pattern, expr)
        var_match_count = len(matches)

        if var_match_count == 0:
            return expr

        # Evaluate all dynamic variables (this return only string value), e.g. '{my_name} is {my_age} years old'
        return re.sub(
            pattern,
            lambda matched_var: str(context.evaluate_python_expression(matched_var.group(1))),
            expr,
        )

    @staticmethod
    def gen_task_load_data_from_source_or_script(
        context: SetupContext,
        stmt: GenerateStatement,
        source_str: str,  # DO NOT remove this parameter, used on EE as well
        separator: str,
        source_scripted: bool,
        processed_data_count: int,  # DO NOT remove this parameter, used on EE as well
        load_start_idx: int,
        load_end_idx: int,
        load_pagination: DataSourcePagination | None,
        source_operation: dict | None,
    ) -> tuple[list[dict], bool]:
        """
        Generate task to load data from source
        """
        build_from_source = True
        root_context = context.root
        source_data: dict | list = []

        # get prefix and suffix
        setup_ctx = context.root if not isinstance(context, SetupContext) else context
        prefix = stmt.variable_prefix or setup_ctx.default_variable_prefix
        suffix = stmt.variable_suffix or setup_ctx.default_variable_suffix

        data_source_registry = root_context.class_factory_util.get_datasource_registry_cls()

        if source_str is None:
            if stmt.script is None:
                build_from_source = False
            else:
                # Evaluate script in source
                source_data = context.evaluate_python_expression(stmt.script)
        # Load data from CSV
        elif source_str.endswith(".csv"):
            source_data = data_source_registry.load_csv_file(
                ctx=context,
                file_path=root_context.descriptor_dir / source_str,
                separator=separator,
                cyclic=stmt.cyclic,
                start_idx=load_start_idx,
                end_idx=load_end_idx,
                source_scripted=source_scripted,
                prefix=prefix,
                suffix=suffix,
            )
        # Load data from JSON
        elif source_str.endswith(".json"):
            source_data = data_source_registry.load_json_file(
                root_context.descriptor_dir / source_str,
                stmt.cyclic,
                load_start_idx,
                load_end_idx,
            )
            # if sourceScripted then evaluate python expression in json
            if source_scripted:
                try:
                    source_data = TaskUtil.evaluate_file_script_template(
                        ctx=context, datas=source_data, prefix=prefix, suffix=suffix
                    )
                except Exception as e:
                    logger.debug(f"Failed to pre-evaluate source script for {stmt.full_name}: {e}")
        # Load data from XML
        elif source_str.endswith(".xml"):
            if source_operation:
                # (EE feature only) Load XML file with source operation
                source_data = data_source_registry.load_xml_file_with_operation(
                    root_context.descriptor_dir / source_str,
                    stmt.cyclic,
                    load_start_idx,
                    load_end_idx,
                    source_operation,
                )
            else:
                source_data = data_source_registry.load_xml_file(
                    root_context.descriptor_dir / source_str, stmt.cyclic, load_start_idx, load_end_idx
                )
            # if sourceScripted then evaluate python expression in json
            if source_scripted:
                source_data = TaskUtil.evaluate_file_script_template(
                    ctx=context, datas=source_data, prefix=prefix, suffix=suffix
                )
        # Load data from in-memory memstore
        elif root_context.memstore_manager.contain(source_str):
            source_data = root_context.memstore_manager.get_memstore(source_str).get_data_by_type(
                stmt.type or stmt.name, load_pagination, stmt.cyclic
            )
        # Load data from client (MongoDB, RDBMS,...)
        elif root_context.clients.get(source_str) is not None:
            client = root_context.clients.get(source_str)
            # Load data from MongoDB
            if isinstance(client, MongoDBClient):
                if stmt.selector:
                    selector = TaskUtil.evaluate_selector_script(context, stmt)
                    source_data = client.get_by_page_with_query(query=selector, pagination=load_pagination)
                elif stmt.type:
                    source_data = client.get_by_page_with_type(collection_name=stmt.type, pagination=load_pagination)
                else:
                    raise ValueError(
                        "MongoDB source requires at least attribute 'type', 'selector' or 'iterationSelector'"
                    )
                # Init empty product for upsert MongoDB in case no record found by query
                if (
                    len(source_data) == 0
                    and isinstance(stmt, GenerateStatement)
                    and stmt.contain_mongodb_upsert(root_context)
                ):
                    source_data = [{}]
            # Load data from RDBMS
            elif isinstance(client, RdbmsClient):
                if stmt.selector:
                    selector = TaskUtil.evaluate_selector_script(context, stmt)
                    source_data = client.get_by_page_with_query(original_query=selector, pagination=load_pagination)
                else:
                    source_data = client.get_by_page_with_type(
                        table_name=stmt.type or stmt.name,
                        pagination=load_pagination,
                    )
            else:
                raise ValueError(f"Cannot load data from client: {type(client).__name__}")
        else:
            raise ValueError(f"cannot find data source {source_str} for iterate task")

        return_source_data = source_data if isinstance(source_data, list) else [source_data]
        return return_source_data, build_from_source

    @staticmethod
    def export_product_by_page(
        root_context: SetupContext,
        stmt: GenerateStatement,
        xml_result: dict[str, list[dict]],
        exporter_state_manager: ExporterStateManager,
    ) -> None:
        """
        Export single page of product in generate statement.

        :param root_context: SetupContext instance.
        :param stmt: GenerateStatement instance.
        :param xml_result: Dictionary of product data.
        :param exporter_state_manager: ExporterStateManager instance.
        :return: None
        """
        # If product is in XML format, convert it to JSON
        json_result = [TaskUtil.convert_xml_dict_to_json_dict(product) for product in xml_result[stmt.full_name]]

        # Wrap product key and value into a tuple
        # for iterate database may have key, value, and other statement attribute info
        if getattr(stmt, "selector", False):
            json_product = (stmt.name, json_result, {"selector": stmt.selector})
        elif getattr(stmt, "type", False):
            json_product = (stmt.name, json_result, {"type": stmt.type})
        else:
            json_product = (stmt.name, json_result)  # type: ignore[assignment]

        # Create a unique cache key incorporating task_id and statement details
        exporters_cache_key = stmt.full_name

        # Get cached exporters
        exporters = root_context.task_exporters[exporters_cache_key]
        exporters["page_count"] += 1

        # Use cached exporters
        # Run exporters with operations first
        for exporter, operation in exporters["with_operation"]:
            if isinstance(exporter, MongoDBExporter) and operation == "upsert":
                json_product = exporter.upsert(product=json_product)
            elif hasattr(exporter, operation):
                getattr(exporter, operation)(json_product)
            else:
                raise ValueError(f"Exporter does not support operation: {exporter}.{operation}")

        task_util_cls = root_context.class_factory_util.get_task_util_cls()

        task_util_cls.exporter_without_operation(
            root_context.task_id,
            json_product,
            xml_result,
            stmt,
            exporters["without_operation"],
            exporter_state_manager,
            exporters["page_count"] == 1,
        )

    @staticmethod
    def exporter_without_operation(
        task_id: str,
        json_product: tuple,
        xml_result: dict,
        stmt: GenerateStatement,
        exporters_without_operation: list,
        exporter_state_manager: ExporterStateManager,
        first_page: bool,
    ):
        # Run exporters without operations
        for exporter in exporters_without_operation:
            try:
                # Skip lazy exporters
                if isinstance(exporter, Memstore):
                    continue
                elif isinstance(exporter, XMLExporter):
                    exporter.consume(
                        (json_product[0], xml_result[stmt.full_name]), stmt.full_name, exporter_state_manager
                    )
                elif isinstance(exporter, JsonExporter | TXTExporter | CSVExporter):
                    exporter.consume(json_product, stmt.full_name, exporter_state_manager)
                else:
                    exporter.consume(json_product)
            except Exception as e:
                # import traceback
                # traceback.print_exc()
                logger.error(f"Error in exporter {type(exporter).__name__}: {str(e)}")
                raise ValueError(f"Error in exporter {type(exporter).__name__}: {e}") from e

    @staticmethod
    def evaluate_selector_script(context: Context, stmt: GenerateStatement):
        """
        Evaluate script selector.

        :param context: Context instance.
        :param stmt: GenerateStatement instance.
        :return: Evaluated selector.
        """
        selector = stmt.selector or ""
        prefix = stmt.variable_prefix or context.root.default_variable_prefix
        suffix = stmt.variable_suffix or context.root.default_variable_suffix
        return TaskUtil.evaluate_variable_concat_prefix_suffix(context, selector, prefix=prefix, suffix=suffix)

    @staticmethod
    def convert_xml_dict_to_json_dict(xml_dict: dict):
        """
        Convert XML dict with #text and @attribute to pure JSON dict.

        :param xml_dict: XML dictionary.
        :return: JSON dictionary.
        """
        if "#text" in xml_dict:
            return xml_dict["#text"]
        res = {}
        for key, value in xml_dict.items():
            if not key.startswith("@"):
                if isinstance(value, dict):
                    res[key] = TaskUtil.convert_xml_dict_to_json_dict(value)
                elif isinstance(value, list):
                    res[key] = [TaskUtil.convert_xml_dict_to_json_dict(v) if isinstance(v, dict) else v for v in value]
                else:
                    res[key] = value
        return res

    @staticmethod
    def is_source_ml_model(stmt: GenerateStatement):
        """
        check if source is model train by ml-train or not
        """
        # Always False in CE cause this is an EE feature
        return False
