# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import copy
import itertools
import logging
from collections.abc import Iterable, Iterator
from pathlib import Path

import xmltodict
from sqlalchemy.exc import OperationalError, ProgrammingError

from datamimic_ce.engine.dsl.api import SourceFileFormat
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.io.contracts import DataSourcePagination
from datamimic_ce.engine.io.file_cache import FileContentStorage
from datamimic_ce.engine.io.files import FileUtil, _is_json_object, _is_json_records

logger = logging.getLogger("DATAMIMIC")


class DataSourceRegistry:
    """File loaders and source paging, with scalar signatures.

    Owns no statement/context knowledge: routing a statement's ``source=`` to one of
    these calls is the runtime's job (``engine.runtime.sources.router``).
    """

    @staticmethod
    def _weighted_csv_has_header(file_path: Path, separator: str) -> bool:
        """Return whether a weighted CSV starts with a non-numeric header row."""
        rows = FileUtil._read_raw_csv(file_path, separator, "utf-8")
        return bool(rows) and len(rows[0]) > 1 and not FileUtil._parses_as_float(rows[0][1])

    @staticmethod
    def _get_source(key: str, csv_separator: str, source_format: SourceFileFormat) -> list[dict]:
        """
        Load source data from file and put into cache
        """
        logger.debug(f"Load source {key} from file")
        # Load source data from file
        if source_format in (SourceFileFormat.CSV, SourceFileFormat.WEIGHTED_ENTITY_CSV):
            return FileUtil.read_csv_to_dict_list(Path(key), csv_separator)
        elif source_format is SourceFileFormat.XLSX:
            return FileUtil.read_xlsx_to_dict_list(Path(key))
        elif source_format is SourceFileFormat.FIXED_WIDTH:
            return FileUtil.read_fixed_width_to_dict_list(Path(key))
        elif source_format is SourceFileFormat.JSON:
            json_data = FileUtil.read_json(Path(key))
            if _is_json_records(json_data):
                return json_data
            elif _is_json_object(json_data):
                return [json_data]
            else:
                raise ValueError(f"JSON file '{key}' must contain a list of objects or a dictionary")
        elif source_format is SourceFileFormat.XML:
            document = FileContentStorage.load_file_with_custom_func(
                key, lambda: xmltodict.parse(Path(key).read_bytes(), attr_prefix="@", cdata_key="#text")
            )
            if not isinstance(document, dict):
                raise ValueError(f"XML source '{key}' must have a document root")
            # <list><item>...</item></list> is a row list; any other document is one row
            root = document.get("list")
            if not isinstance(root, dict) or root.get("item") is None:
                return [document]
            items = root["item"] if isinstance(root["item"], list) else [root["item"]]
            if not all(isinstance(item, dict) for item in items):
                raise ValueError(
                    f"XML source '{key}': every <list><item> must contain child elements to form a row, "
                    f"got a text-only <item>"
                )
            return items
        else:
            raise ValueError(f"Data source '{key}' is not supported is not handled by DataSourceRegistry")

    @staticmethod
    def rdbms_count_query_length(client: RdbmsClient, query: str, source_str: str, query_label: str) -> int | None:
        """Row count for one RDBMS length-probe query; ``None`` on a query failure (already
        logged at ERROR). sqlalchemy's exception types are an io-only concern - the caller
        (the runtime's source router) only ever sees the int|None result."""
        try:
            return client.count_query_length(query=query)
        except (ProgrammingError, OperationalError):
            logger.error(f"Cannot get length of database source '{source_str}' with {query_label} '{query}'")
            return None

    @staticmethod
    def get_cyclic_data_list(
        data: Iterable, pagination: DataSourcePagination | None, cyclic: bool = False, offset: int = 0
    ) -> list:
        """
        Get cyclic data from iterable data source. ``offset`` drops the first N rows BEFORE any
        windowing, so page windows and a cyclic wrap both operate strictly on the post-offset
        region (a wrap must never re-include skipped rows).
        """
        if offset:
            data = list(data)[offset:]
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
    def load_csv_file(
        file_path: Path,
        separator: str,
        cyclic: bool | None,
        start_idx: int | None,
        end_idx: int | None,
        offset: int = 0,
    ) -> list[dict]:
        """
        Load CSV content from file with skip and limit.

        :param file_path: Path to the CSV file.
        :param separator: CSV delimiter.
        :param cyclic: Whether to cycle through data.
        :param start_idx: Starting index.
        :param end_idx: Ending index.
        :param offset: Rows to drop from the start of the file before windowing.
        :return: List of dictionaries representing CSV rows.
        """
        cyclic = cyclic if cyclic is not None else False

        file_data = DataSourceRegistry._get_source(str(file_path), separator, SourceFileFormat.CSV)
        pagination = (
            DataSourcePagination(start_idx, end_idx - start_idx)
            if (start_idx is not None and end_idx is not None)
            else None
        )
        return DataSourceRegistry.get_cyclic_data_list(
            data=file_data, cyclic=cyclic, pagination=pagination, offset=offset
        )

    @staticmethod
    def load_json_file(
        file_path: Path, cyclic: bool | None, start_idx: int | None, end_idx: int | None, offset: int = 0
    ) -> list[dict]:
        """
        Load JSON content from file using skip and limit.

        :param file_path: Path to the JSON file.
        :param cyclic: Whether to cycle through data.
        :param start_idx: Starting index.
        :param end_idx: Ending index.
        :param offset: Rows to drop from the start of the file before windowing.
        :return: List of dictionaries representing JSON objects.
        """
        cyclic = cyclic if cyclic is not None else False

        file_data = DataSourceRegistry._get_source(str(file_path), ",", SourceFileFormat.JSON)

        # Validate the JSON data
        if not isinstance(file_data, list):
            raise ValueError(f"JSON file '{file_path.name}' must contain a list of objects")
        pagination = (
            DataSourcePagination(start_idx, end_idx - start_idx)
            if (start_idx is not None and end_idx is not None)
            else None
        )
        return DataSourceRegistry.get_cyclic_data_list(
            data=file_data, cyclic=cyclic, pagination=pagination, offset=offset
        )

    @staticmethod
    def load_xlsx_file(
        file_path: Path, cyclic: bool | None, start_idx: int | None, end_idx: int | None, offset: int = 0
    ) -> list[dict]:
        """Load an .xlsx sheet (first row = header) as a paginated, optionally cyclic list of dicts."""
        file_data = DataSourceRegistry._get_source(str(file_path), ",", SourceFileFormat.XLSX)
        pagination = (
            DataSourcePagination(start_idx, end_idx - start_idx)
            if (start_idx is not None and end_idx is not None)
            else None
        )
        return DataSourceRegistry.get_cyclic_data_list(
            data=file_data, cyclic=cyclic if cyclic is not None else False, pagination=pagination, offset=offset
        )

    @staticmethod
    def load_fixed_width_file(
        file_path: Path, cyclic: bool | None, start_idx: int | None, end_idx: int | None, offset: int = 0
    ) -> list[dict]:
        """Load a self-describing .fcw file as a paginated, optionally cyclic list of dicts."""
        file_data = DataSourceRegistry._get_source(str(file_path), ",", SourceFileFormat.FIXED_WIDTH)
        pagination = (
            DataSourcePagination(start_idx, end_idx - start_idx)
            if (start_idx is not None and end_idx is not None)
            else None
        )
        return DataSourceRegistry.get_cyclic_data_list(
            data=file_data, cyclic=cyclic if cyclic is not None else False, pagination=pagination, offset=offset
        )

    @staticmethod
    def load_xml_file(
        file_path: Path, cyclic: bool | None, start_idx: int | None, end_idx: int | None, offset: int = 0
    ) -> list[dict]:
        """
        Load XML content from file using skip and limit.

        :param file_path: Path to the XML file.
        :param cyclic: Whether to cycle through data.
        :param start_idx: Starting index.
        :param end_idx: Ending index.
        :param offset: Rows to drop from the start of the file before windowing.
        :return: List of dictionaries representing XML items.
        """
        cyclic = cyclic if cyclic is not None else False
        # Read the XML data from a file
        items = DataSourceRegistry._get_source(str(file_path), ",", SourceFileFormat.XML)

        # Apply pagination if needed
        pagination = (
            DataSourcePagination(start_idx, end_idx - start_idx)
            if (start_idx is not None and end_idx is not None)
            else None
        )
        return DataSourceRegistry.get_cyclic_data_list(data=items, cyclic=cyclic, pagination=pagination, offset=offset)

    @staticmethod
    def load_xml_file_with_operation(
        file_path: Path,
        cyclic: bool | None,
        start_idx: int | None,
        end_idx: int,
    ):
        """
        (EE feature only)
        Load XML content from file using skip and limit.
        """
        pass
