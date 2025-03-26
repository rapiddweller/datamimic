# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import copy
import itertools
import random
from collections.abc import Iterable, Iterator
from pathlib import Path

import xmltodict
from sqlalchemy.exc import OperationalError, ProgrammingError

from datamimic_ce.clients.mongodb_client import MongoDBClient
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.logger import logger
from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.statements.reference_statement import ReferenceStatement
from datamimic_ce.statements.statement import Statement
from datamimic_ce.utils.file_content_storage import FileContentStorage
from datamimic_ce.utils.file_util import FileUtil


class DataSourceRegistry:
    @staticmethod
    def _get_source(key: str, csv_separator: str = ",") -> list[dict]:
        """
        Load source data from file and put into cache
        """
        logger.debug(f"Load source {key} from file")
        # Load source data from file
        if key.endswith(".csv"):
            return FileUtil.read_csv_to_dict_list(Path(key), csv_separator)
        elif key.endswith(".json"):
            json_data = FileUtil.read_json(Path(key))
            if isinstance(json_data, list):
                return json_data
            elif isinstance(json_data, dict):
                return [json_data]
            else:
                raise ValueError(f"JSON file '{key}' must contain a list of objects or a dictionary")
        elif key.endswith(".xml"):
            return FileContentStorage.load_file_with_custom_func(
                key, lambda: xmltodict.parse(open(key).read(), attr_prefix="@", cdata_key="#text")
            )
        else:
            raise ValueError(f"Data source '{key}' is not supported is not handled by DataSourceRegistry")

    @staticmethod
    def set_data_source_length(ctx: SetupContext | GenIterContext, stmt: Statement) -> None:
        """
        Calculate length of data source then save into context
        :param ctx:
        :param stmt:
        :return:
        """
        # TODO: consider to paginate source of element "reference"
        if isinstance(stmt, ReferenceStatement):
            return

        root_ctx = ctx.root
        source_id: str | None = stmt.full_name
        ds_len: int = 0

        # Check if data source length is already set
        if root_ctx.data_source_len.get(source_id, None) is not None:
            return

        # Check length of script data
        if isinstance(stmt, GenerateStatement) and stmt.script is not None:
            try:
                ds_len = len(ctx.evaluate_python_expression(stmt.script))
            except Exception as e:
                logger.debug(f"Cannot get length of script data before generating data: {e}")
                return
        # Check length of data source
        else:
            # Check if prop source is available
            if hasattr(stmt, "source"):
                source_str = stmt.source
                if source_str is None:
                    return
            else:
                return
            # Try to evaluate script as source string
            # Ignore to check scripted source if eval failed in pre-execute task
            if source_str.startswith("{") and source_str.endswith("}"):
                try:
                    source_str = eval(source_str[1:-1])
                except:  # noqa: E722
                    return

            # 2: Get source info from ctx client (e.g. checking if it is SQL, MongoDB or CSV source)

            # Check if source is data source file or database collection/table
            # 2.1: Check if datasource is csv file
            if source_str.endswith(".csv") or source_str.endswith(".json") or source_str.endswith(".xml"):
                ds_len = len(
                    DataSourceRegistry._get_source(
                        str(root_ctx.descriptor_dir / source_str),
                        (getattr(stmt, "separator", None) or ctx.root.default_separator),
                    )
                )
            # 2.4: Check if datasource is memstore
            elif root_ctx.memstore_manager.contain(source_str) and hasattr(stmt, "type"):
                ds_len = root_ctx.memstore_manager.get_memstore(source_str).get_data_len_by_type(stmt.type or stmt.name)
            elif root_ctx.get_client_by_id(source_str) is not None:
                client = root_ctx.get_client_by_id(source_str)
                if client is None:
                    raise ValueError(
                        f"Client '{source_str}' could not be found in your context, please check your script"
                    )
                # handle database collection/table as data source
                from datamimic_ce.clients.rdbms_client import RdbmsClient

                if isinstance(client, RdbmsClient) and hasattr(stmt, "selector"):
                    if stmt.selector is not None:
                        try:
                            ds_len = client.count_query_length(query=stmt.selector)
                        except ProgrammingError:
                            logger.error(
                                f"Cannot get length of database source '{source_str}' with selector '{stmt.selector}'"
                            )
                            return
                        except OperationalError:
                            logger.error(
                                f"Cannot get length of database source '{source_str}' with selector '{stmt.selector}'"
                            )
                            return
                    elif hasattr(stmt, "iteration_selector") and stmt.iteration_selector is not None:
                        try:
                            ds_len = client.count_query_length(query=stmt.iteration_selector)
                        except ProgrammingError:
                            logger.error(
                                f"Cannot get length of database source '{source_str}' "
                                f"with iterationSelector '{stmt.iteration_selector}'"
                            )
                            return
                        except OperationalError:
                            logger.error(
                                f"Cannot get length of database source '{source_str}' "
                                f"with iterationSelector '{stmt.iteration_selector}'"
                            )
                            return
                    elif hasattr(stmt, "type") and stmt.type is not None:
                        ds_len = client.count_table_length(table_name=str(stmt.type) or str(stmt.name))

                elif isinstance(client, MongoDBClient) and hasattr(stmt, "selector") and hasattr(stmt, "type"):
                    if stmt.selector is not None:
                        try:
                            ds_len = client.count_query_length(stmt.selector)
                        except ValueError:
                            return
                    elif stmt.type is not None:
                        try:
                            ds_len = client.count(collection_name=stmt.type)
                        except ValueError:
                            return
                    elif hasattr(stmt, "iteration_selector") and stmt.iteration_selector is not None:
                        try:
                            ds_len = client.count_query_length(query=stmt.iteration_selector)
                        except ValueError:
                            logger.error(
                                f"Cannot get length of database source '{source_str}' "
                                f"with iterationSelector '{stmt.iteration_selector}'"
                            )
                            return
                    else:
                        raise ValueError(
                            "MongoDB source requires at least attribute 'type', 'selector' or 'iterationSelector'"
                        )
                else:
                    raise ValueError(f"Cannot determine type of client '{source_id}.{source_str}'")
            else:
                logger.warning(f"Data source '{source_str}' is not supported for length calculation")
                return

        # 3: Set length of data source
        root_ctx.data_source_len[source_id] = ds_len

    @staticmethod
    def get_cyclic_data_list(data: Iterable, pagination: DataSourcePagination | None, cyclic: bool = False) -> list:
        """
        Get cyclic data from iterable data source
        """
        if pagination is None:
            start_idx = 0
            end_idx = len(list(data))
        else:
            start_idx = pagination.skip
            end_idx = pagination.skip + pagination.limit

        if cyclic:
            iterator = itertools.cycle(data)
            return [copy.deepcopy(ele) for ele in itertools.islice(iterator, start_idx, end_idx)]
        else:
            return list(itertools.islice(data, start_idx, end_idx))

    @staticmethod
    def get_cyclic_data_iterator(
        data: Iterable, pagination: DataSourcePagination | None, cyclic: bool | None = False
    ) -> Iterator | None:
        """
        Get cyclic iterator from iterable data source
        """
        if pagination is None:
            start_idx = 0
            end_idx = len(list(data))
        else:
            start_idx = pagination.skip
            end_idx = pagination.skip + pagination.limit

        if cyclic:
            iterator = itertools.cycle(data)
            return itertools.cycle(list(itertools.islice(iterator, start_idx, end_idx))[: end_idx - start_idx])
        else:
            return itertools.islice(data, start_idx, end_idx)

    @staticmethod
    def get_shuffled_data_with_cyclic(
        data: Iterable, pagination: DataSourcePagination | None, cyclic: bool | None, seed: int
    ) -> list:
        """
        Get shuffled data from iterable data source
        """
        source_len = len(list(data))
        # If source is empty, return empty list
        if source_len == 0:
            return []

        # If pagination is None, get all data
        if pagination is None:
            start_idx = 0
            end_idx = len(list(data))
        # If pagination is not None, get data based on pagination
        else:
            start_idx = pagination.skip
            end_idx = pagination.skip + pagination.limit

        # If not cyclic, return data limited by datasource len
        if not cyclic:
            end_idx = min(end_idx, source_len)

        # Update seed for each new random batch of datasource
        current_seed = seed + int(start_idx / source_len)
        current_idx = start_idx

        res: list = []
        # Check if amount of returned data is enough
        # Extend data until len of result is larger than page len and higher than end_idx
        while len(res) <= end_idx - start_idx or len(res) < (start_idx % source_len) + end_idx - start_idx:
            # Get shuffled data from datasource
            random.seed(current_seed)
            shuffle_data = list(data)
            random.shuffle(shuffle_data)

            # Append shuffled data to result
            res.extend(shuffle_data)

            # Update current index and seed
            current_idx += source_len
            current_seed += 1

        start_idx_cap = start_idx % source_len
        return res[start_idx_cap : start_idx_cap + end_idx - start_idx]

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

        :param ctx: SetupContext
        :param file_path: Path to the CSV file.
        :param separator: CSV delimiter.
        :param cyclic: Whether to cycle through data.
        :param start_idx: Starting index.
        :param end_idx: Ending index.
        :return: List of dictionaries representing CSV rows.
        """
        cyclic = cyclic if cyclic is not None else False

        file_data = DataSourceRegistry._get_source(str(file_path), separator)
        pagination = (
            DataSourcePagination(start_idx, end_idx - start_idx)
            if (start_idx is not None and end_idx is not None)
            else None
        )
        result = DataSourceRegistry.get_cyclic_data_list(data=file_data, cyclic=cyclic, pagination=pagination)

        # if sourceScripted then evaluate python expression in csv
        if source_scripted:
            from datamimic_ce.tasks.task_util import TaskUtil

            evaluated_result = TaskUtil.evaluate_file_script_template(
                ctx=ctx, datas=result, prefix=prefix, suffix=suffix
            )
            return evaluated_result if isinstance(evaluated_result, list) else [evaluated_result]

        return result

    @staticmethod
    def load_json_file(file_path: Path, cyclic: bool | None, start_idx: int, end_idx: int) -> list[dict]:
        """
        Load JSON content from file using skip and limit.

        :param file_path: Path to the JSON file.
        :param cyclic: Whether to cycle through data.
        :param start_idx: Starting index.
        :param end_idx: Ending index.
        :return: List of dictionaries representing JSON objects.
        """
        cyclic = cyclic if cyclic is not None else False

        file_data = DataSourceRegistry._get_source(str(file_path))

        # Validate the JSON data
        if not isinstance(file_data, list):
            raise ValueError(f"JSON file '{file_path.name}' must contain a list of objects")
        pagination = (
            DataSourcePagination(start_idx, end_idx - start_idx)
            if (start_idx is not None and end_idx is not None)
            else None
        )
        return DataSourceRegistry.get_cyclic_data_list(data=file_data, cyclic=cyclic, pagination=pagination)

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
        file_data = DataSourceRegistry._get_source(str(file_path))
        # Handle the case where data might be None
        if file_data is None:
            return []

        # Extract items from list structure if present
        if isinstance(file_data, dict) and file_data.get("list") and file_data.get("list", {}).get("item"):
            items = file_data["list"]["item"]
        else:
            items = file_data

        # Convert single item to list if needed
        if isinstance(items, dict):
            items = [items]
        elif not isinstance(items, list):
            items = []

        # Apply pagination if needed
        pagination = (
            DataSourcePagination(start_idx, end_idx - start_idx)
            if (start_idx is not None and end_idx is not None)
            else None
        )
        return DataSourceRegistry.get_cyclic_data_list(data=items, cyclic=cyclic, pagination=pagination)

    @staticmethod
    def load_xml_file_with_operation(
        file_path: Path, cyclic: bool | None, start_idx: int, end_idx: int, source_operation: dict | None
    ):
        """
        (EE feature only)
        Load XML content from file using skip and limit.
        """
        pass
