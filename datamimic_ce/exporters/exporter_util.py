# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import ast
import json
import re
from datetime import date, datetime
from decimal import Decimal

import numpy
from bson import ObjectId

from datamimic_ce.clients.client import Client
from datamimic_ce.clients.mongodb_client import MongoDBClient
from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.constants.exporter_constants import (
    EXPORTER_CONSOLE_EXPORTER,
    EXPORTER_CSV,
    EXPORTER_JSON,
    EXPORTER_JSON_SINGLE,
    EXPORTER_LOG_EXPORTER,
    EXPORTER_TEST_RESULT_EXPORTER,
    EXPORTER_TXT,
    EXPORTER_XML,
)
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.exporters.console_exporter import ConsoleExporter
from datamimic_ce.exporters.csv_exporter import CSVExporter
from datamimic_ce.exporters.database_exporter import DatabaseExporter
from datamimic_ce.exporters.exporter import Exporter
from datamimic_ce.exporters.json_exporter import JsonExporter
from datamimic_ce.exporters.log_exporter import LogExporter
from datamimic_ce.exporters.mongodb_exporter import MongoDBExporter
from datamimic_ce.exporters.txt_exporter import TXTExporter
from datamimic_ce.exporters.xml_exporter import XMLExporter
from datamimic_ce.logger import logger
from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.utils.multiprocessing_page_info import MultiprocessingPageInfo


def custom_serializer(obj) -> str:
    """
    Custom serializer for json dump
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    elif isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, numpy.int64):
        return str(numpy.int64)
    elif isinstance(obj, bool | numpy.bool_ | Decimal | set):
        return str(obj)
    raise TypeError(f"Failed when serializing exporting data: Object of type {type(obj)} is not JSON serializable")


class ExporterUtil:
    @staticmethod
    def create_exporter_list(
        setup_context: SetupContext,
        stmt: GenerateStatement,
        targets: list[str],
        page_info: MultiprocessingPageInfo,
    ) -> tuple[list[tuple[Exporter, str]], list[Exporter]]:
        """
        Create list of consumers with and without operation from consumer string

        :param setup_context:
        :param stmt:
        :param targets:
        :return:
        """
        consumers_with_operation = []
        consumers_without_operation = []

        exporter_str_list = list(targets)

        # Join the list back into a string
        target_str = ",".join(exporter_str_list)

        # Parse the target string using the parse_function_string function
        try:
            parsed_targets = ExporterUtil.parse_function_string(target_str)
        except ValueError as e:
            raise ValueError(f"Error parsing target string: {e}") from e

        # Now loop over the parsed functions and create exporters
        for target in parsed_targets:
            exporter_name = target["function_name"]
            params = target.get("params") or {}
            # Handle consumer with operation
            if "." in exporter_name:
                consumer_name, operation = exporter_name.split(".", 1)
                client = setup_context.get_client_by_id(consumer_name)
                consumer = ExporterUtil._create_exporter_from_client(client, consumer_name)
                consumers_with_operation.append((consumer, operation))
            # Handle consumer without operation
            else:
                consumer = ExporterUtil.get_exporter_by_name(
                    setup_context=setup_context,
                    name=exporter_name,
                    product_name=stmt.name,
                    page_info=page_info,
                    exporter_params_dict=params,
                )
                if consumer is not None:
                    consumers_without_operation.append(consumer)

        return consumers_with_operation, consumers_without_operation

    @staticmethod
    def parse_function_string(function_string):
        parsed_functions = []
        # Remove spaces and check if only commas or blank string are provided
        if function_string.strip() == "" or all(char in ", " for char in function_string):
            return parsed_functions

        # Wrap the function string in a list to make it valid Python code
        code_to_parse = f"[{function_string}]"

        try:
            # Parse the code into an AST node
            module = ast.parse(code_to_parse, mode="eval")
        except SyntaxError as e:
            raise ValueError(f"Error parsing function string: {e}") from e

        # Ensure the parsed node is a list
        if not isinstance(module.body, ast.List):
            raise ValueError("Function string is not a valid list of function calls.")

        # Iterate over each element in the list
        for element in module.body.elts:
            # Handle function calls with parameters
            if isinstance(element, ast.Call):
                # Extract function name, including dot notation (e.g., mongodb.upsert)
                if isinstance(element.func, ast.Name):
                    function_name = element.func.id
                elif isinstance(element.func, ast.Attribute):
                    # Capture the full dotted name
                    parts = []
                    current = element.func
                    while isinstance(current, ast.Attribute):
                        parts.append(current.attr)
                        current = current.value
                    if isinstance(current, ast.Name):
                        parts.append(current.id)
                    function_name = ".".join(reversed(parts))
                else:
                    raise ValueError("Unsupported function type in function call.")

                params = {}
                # Extract keyword arguments
                for keyword in element.keywords:
                    key = keyword.arg
                    try:
                        # Safely evaluate the value using ast.literal_eval
                        value = ast.literal_eval(keyword.value)
                    except (ValueError, SyntaxError):
                        # If evaluation fails, raise error for non-literal parameters
                        raise ValueError(f"Non-literal parameter found: {keyword.value}") from None
                    params[key] = value

                parsed_functions.append({"function_name": function_name, "params": params})
            # Handle function names without parameters, including dotted names like mongodb.delete
            elif isinstance(element, ast.Attribute):
                # For dotted names like mongodb.delete
                parts = []
                current = element
                while isinstance(current, ast.Attribute):
                    parts.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    parts.append(current.id)
                function_name = ".".join(reversed(parts))
                parsed_functions.append({"function_name": function_name, "params": None})
            elif isinstance(element, ast.Name):
                # For single names like CSV
                function_name = element.id
                parsed_functions.append({"function_name": function_name, "params": None})
            elif isinstance(element, ast.Constant):  # For Python 3.8+, for older versions use ast.Str or ast.Num
                # This handles cases like 'CSV' and 'JSON' if they are given as strings
                function_name = element.value
                parsed_functions.append({"function_name": function_name, "params": None})
            else:
                # Attempt to evaluate other expressions (e.g., strings, numbers)
                try:
                    value = ast.literal_eval(element)
                    function_name = str(value)
                    parsed_functions.append({"function_name": function_name, "params": None})
                except Exception:
                    raise ValueError("Unsupported expression in function string.") from None

        return parsed_functions

    @staticmethod
    def get_exporter_by_name(
        setup_context: SetupContext,
        name: str,
        product_name: str,
        page_info: MultiprocessingPageInfo,
        exporter_params_dict: dict,
    ):
        """
        Consumer factory: Create consumer based on name

        :param setup_context:
        :param name:
        :return:
        """
        if name is None or name == "":
            return None

        chunk_size = exporter_params_dict.get("chunk_size")
        use_ndjson = exporter_params_dict.get("use_ndjson")
        fieldnames = exporter_params_dict.get("fieldnames")
        delimiter = exporter_params_dict.get("delimiter")
        quotechar = exporter_params_dict.get("quotechar")
        quoting = exporter_params_dict.get("quoting")
        line_terminator = exporter_params_dict.get("line_terminator")
        root_element = exporter_params_dict.get("root_element")
        item_element = exporter_params_dict.get("item_element")
        encoding = exporter_params_dict.get("encoding")
        if fieldnames is not None and isinstance(fieldnames, str):
            try:
                fieldnames = ast.literal_eval(fieldnames)
            except Exception as e:
                raise ValueError(f"Error parsing fieldnames {fieldnames}: {e}") from e

        elif name == EXPORTER_CONSOLE_EXPORTER:
            return ConsoleExporter()
        elif name == EXPORTER_LOG_EXPORTER:
            return LogExporter()
        elif name == EXPORTER_JSON:
            return JsonExporter(setup_context, product_name, page_info, chunk_size, use_ndjson, encoding)
        elif name == EXPORTER_CSV:
            return CSVExporter(
                setup_context,
                product_name,
                page_info,
                chunk_size,
                fieldnames,
                delimiter,
                quotechar,
                quoting,
                line_terminator,
                encoding,
            )
        elif name == EXPORTER_XML:
            return XMLExporter(setup_context, product_name, page_info, chunk_size, root_element, item_element, encoding)
        elif name == EXPORTER_TXT:
            return TXTExporter(setup_context, product_name, page_info, chunk_size, delimiter, line_terminator, encoding)
        elif name == EXPORTER_TEST_RESULT_EXPORTER:
            return setup_context.test_result_exporter
        elif name in setup_context.clients:
            # 1. get client from context
            client = setup_context.get_client_by_id(name)
            # 2. create consumer from client
            return ExporterUtil._create_exporter_from_client(client, name)
        elif setup_context.memstore_manager.contain(name):
            return setup_context.memstore_manager.get_memstore(name)
        else:
            raise ValueError(
                f"Target not found: {name}, please check the target name again. "
                f"Expected: {EXPORTER_JSON}, {EXPORTER_CSV}, {EXPORTER_XML}, "
                f"{EXPORTER_TXT}, {EXPORTER_TEST_RESULT_EXPORTER}, {EXPORTER_JSON_SINGLE}, "
                f"{EXPORTER_CONSOLE_EXPORTER}, {EXPORTER_LOG_EXPORTER}, "
                f"or client {list(setup_context.clients.keys())} "
                f"or memstore {setup_context.memstore_manager.get_memstores_list()}"
            )

    @staticmethod
    def _create_exporter_from_client(client: Client, client_name: str):
        if isinstance(client, MongoDBClient):
            return MongoDBExporter(client)
        elif isinstance(client, RdbmsClient):
            return DatabaseExporter(client)
        else:
            raise ValueError(f"Cannot create target for client {client_name}")

    @staticmethod
    def json_dumps(data: object, indent=4) -> str:
        """
        JSON dump with default custom serializer
        """
        return json.dumps(data, default=custom_serializer, ensure_ascii=False, indent=indent)

    @staticmethod
    def check_path_format(path) -> str:
        """
        Check if the targetUri path is a valid file or directory path
        :param path:
        :return: "file" if the path is a file path, "directory" if the path is a directory path
        """
        logger.debug(f"Checking targetUri path format: {path}")
        # Regex to validate the path with only forward slashes and valid characters
        if re.match(r"^[a-zA-Z0-9_\-\.\/]+$", path):
            # Check for invalid path ending (should not end with a dot)
            if path.endswith("."):
                logger.debug("Invalid path format")
                raise ValueError(f"Invalid targetUri path format {path}")
            # Check for file extension: one or more characters after a dot, and not ending with a dot
            elif re.search(r"\.[a-zA-Z0-9]+$", path):
                logger.debug(f"File path format detected: {path}")
                return "file"
            # Check for path with only slashes
            elif all(char == "/" for char in path):
                logger.debug("Invalid path format: path contains only slashes")
                raise ValueError(f"Invalid targetUri path format {path}")
            else:
                logger.debug(f"Directory path format detected: {path}")
                return "directory"
        else:
            raise ValueError(f"Invalid targetUri path format {path}")
