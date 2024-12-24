# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import copy
import itertools
import json
import random
import xml.etree.ElementTree as ET
from collections.abc import Iterable, Iterator
from pathlib import Path

from sqlalchemy.exc import OperationalError, ProgrammingError

from datamimic_ce.clients.mongodb_client import MongoDBClient
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.logger import logger
from datamimic_ce.statements.reference_statement import ReferenceStatement
from datamimic_ce.statements.statement import Statement
from datamimic_ce.utils.in_memory_cache_util import InMemoryCache


class DataSourceUtil:
    @staticmethod
    def set_data_source_length(ctx: SetupContext, stmt: Statement) -> None:
        """
        Calculate length of data source then save into context
        :param ctx:
        :param stmt:
        :return:
        """
        # TODO: consider to paginate source of element "reference"
        if isinstance(stmt, ReferenceStatement):
            return
        # 1: Check if prop source is available
        if not hasattr(stmt, "source") or stmt.source is None:
            return
        if hasattr(stmt, "source"):
            source_str = stmt.source
        source_id: str | None = stmt.full_name
        ds_len: int = 0
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
        if source_str.endswith(".csv"):
            ds_len = DataSourceUtil._count_lines_in_csv(ctx.descriptor_dir / source_str)
        # 2.2: Check if datasource is json file
        elif source_str.endswith(".json"):
            ds_len = DataSourceUtil._count_object_in_json(ctx.task_id, ctx.descriptor_dir / source_str)
        # 2.3: Check if datasource is xml file
        elif source_str.endswith(".xml"):
            ds_len = len(list(ET.parse(ctx.descriptor_dir / source_str).getroot()))
        # 2.4: Check if datasource is memstore
        elif ctx.memstore_manager.contain(source_str) and hasattr(stmt, "type"):
            ds_len = ctx.memstore_manager.get_memstore(source_str).get_data_len_by_type(stmt.type or stmt.name)
        elif ctx.get_client_by_id(source_str) is not None:
            client = ctx.get_client_by_id(source_str)
            if client is None:
                raise ValueError(f"Client '{source_str}' could not be found in your context, please check your script")
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
        ctx.data_source_len[source_id] = ds_len

    @staticmethod
    def _count_lines_in_csv(file_path: Path) -> int:
        """
        Count number of rows in csv file
        :param file_path:
        :return:
        """
        with file_path.open("r") as csvfile:
            line_count = sum(1 for _ in csvfile)
        return line_count

    @staticmethod
    def _count_object_in_json(task_id: str, file_path: Path) -> int:
        """
        Count number of objects in json file
        :param file_path:
        :return:
        """
        # Try to load JSON data from InMemoryCache
        in_mem_cache = InMemoryCache()
        # Add task_id to redis_key for testing lib without platform
        in_mem_cache_key = str(file_path) if task_id in str(file_path) else f"{task_id}_{str(file_path)}"
        in_mem_cache_data = in_mem_cache.get(in_mem_cache_key)
        if in_mem_cache_data:
            data = json.loads(in_mem_cache_data)
        else:
            # Read the JSON data from a file and store it in redis
            with file_path.open("r") as file:
                data = json.load(file)
            # Store data in redis for 24 hours
            in_mem_cache.set(str(file_path), json.dumps(data))

        # Get the length of the JSON content
        return len(data)

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
