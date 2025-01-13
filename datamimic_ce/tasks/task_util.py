# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import csv
import json
import re
from collections import OrderedDict
from pathlib import Path
from typing import Any

import xmltodict

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
from datamimic_ce.data_sources.data_source_util import DataSourceUtil
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
from datamimic_ce.tasks.task import Task
from datamimic_ce.utils.in_memory_cache_util import InMemoryCache
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
    def gen_task_load_data_from_source(
            context: SetupContext,
            stmt: GenerateStatement,
            source_str: str,
            separator: str,
            source_scripted: bool,
            processed_data_count: int,
            load_start_idx: int,
            load_end_idx: int,
            load_pagination: DataSourcePagination | None,
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

        if source_str is None:
            build_from_source = False
        # Load data from CSV
        elif source_str.endswith(".csv"):
            source_data = TaskUtil.load_csv_file(
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
            source_data = TaskUtil.load_json_file(
                root_context.task_id,
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
            source_data = TaskUtil.load_xml_file(
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
        json_result = [GenerateTask.convert_xml_dict_to_json_dict(product) for product in xml_result[stmt.full_name]]

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

        # Get or create exporters
        if exporters_cache_key not in root_context.task_exporters:
            # Create the exporter set once
            exporters_set = stmt.targets.copy()

            # Create exporters with operations
            (
                consumers_with_operation,
                consumers_without_operation,
            ) = root_context.class_factory_util.get_exporter_util().create_exporter_list(
                setup_context=root_context,
                stmt=stmt,
                targets=list(exporters_set),
            )

            # Cache the exporters
            root_context.task_exporters[exporters_cache_key] = {
                "with_operation": consumers_with_operation,
                "without_operation": consumers_without_operation,
                "page_count": 0,  # Track number of pages processed
            }

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

        # Run exporters without operations
        for exporter in exporters["without_operation"]:
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
                logger.error(f"Error in exporter {type(exporter).__name__}: {str(e)}")
                raise ValueError(f"Error in exporter {type(exporter).__name__}") from e

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
    def load_csv_file(
            ctx: SetupContext,
            file_path: Path,
            separator: str,
            cyclic: bool | None,
            start_idx: int,
            end_idx: int,
            source_scripted: bool,
            prefix: str,
            suffix: str,
    ) -> list[dict]:
        """
        Load CSV content from file with skip and limit.

        :param file_path: Path to the CSV file.
        :param separator: CSV delimiter.
        :param cyclic: Whether to cycle through data.
        :param start_idx: Starting index.
        :param end_idx: Ending index.
        :return: List of dictionaries representing CSV rows.
        """
        cyclic = cyclic if cyclic is not None else False

        with file_path.open(newline="") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=separator)
            pagination = (
                DataSourcePagination(start_idx, end_idx - start_idx)
                if (start_idx is not None and end_idx is not None)
                else None
            )
            result = DataSourceUtil.get_cyclic_data_list(data=list(reader), cyclic=cyclic, pagination=pagination)

            # if sourceScripted then evaluate python expression in csv
            if source_scripted:
                evaluated_result = TaskUtil.evaluate_file_script_template(
                    ctx=ctx, datas=result, prefix=prefix, suffix=suffix
                )
                return evaluated_result if isinstance(evaluated_result, list) else [evaluated_result]

            return result

    @staticmethod
    def load_json_file(task_id: str, file_path: Path, cyclic: bool | None, start_idx: int, end_idx: int) -> list[dict]:
        """
        Load JSON content from file using skip and limit.

        :param file_path: Path to the JSON file.
        :param cyclic: Whether to cycle through data.
        :param start_idx: Starting index.
        :param end_idx: Ending index.
        :return: List of dictionaries representing JSON objects.
        """
        cyclic = cyclic if cyclic is not None else False

        # Try to load JSON data from InMemoryCache
        in_mem_cache = InMemoryCache()
        # Add task_id to cache_key for testing lib without platform
        cache_key = str(file_path) if task_id in str(file_path) else f"{task_id}_{str(file_path)}"
        cache_data = in_mem_cache.get(cache_key)
        if cache_data:
            data = json.loads(cache_data)
        else:
            # Read the JSON data from a file and store it in redis
            with file_path.open("r") as file:
                data = json.load(file)
            # Store data in redis for 24 hours
            in_mem_cache.set(str(file_path), json.dumps(data))

        if not isinstance(data, list):
            raise ValueError(f"JSON file '{file_path.name}' must contain a list of objects")
        pagination = (
            DataSourcePagination(start_idx, end_idx - start_idx)
            if (start_idx is not None and end_idx is not None)
            else None
        )
        return DataSourceUtil.get_cyclic_data_list(data=data, cyclic=cyclic, pagination=pagination)

    @staticmethod
    def load_xml_file(file_path: Path, cyclic: bool | None, start_idx: int, end_idx: int) -> list[dict]:
        """
        Load XML content from file using skip and limit.

        :param file_path: Path to the XML file.
        :param cyclic: Whether to cycle through data.
        :param start_idx: Starting index.
        :param end_idx: Ending index.
        :return: List of dictionaries representing XML items.
        """
        cyclic = cyclic if cyclic is not None else False
        # Read the XML data from a file
        with file_path.open("r") as file:
            data = xmltodict.parse(file.read(), attr_prefix="@", cdata_key="#text")
            # Handle the case where data might be None
            if data is None:
                return []

            # Extract items from list structure if present
            if isinstance(data, dict) and data.get("list") and data.get("list", {}).get("item"):
                items = data["list"]["item"]
            else:
                items = data

            # Convert single item to list if needed
            if isinstance(items, OrderedDict):
                items = [items]
            elif not isinstance(items, list):
                items = []

            # Apply pagination if needed
            pagination = (
                DataSourcePagination(start_idx, end_idx - start_idx)
                if (start_idx is not None and end_idx is not None)
                else None
            )
            return DataSourceUtil.get_cyclic_data_list(data=items, cyclic=cyclic, pagination=pagination)
