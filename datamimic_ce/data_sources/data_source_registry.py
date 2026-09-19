# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import copy
import itertools
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from random import Random
from typing import Any, Literal

import xmltodict
from sqlalchemy.exc import OperationalError, ProgrammingError

from datamimic_ce.clients.database_client import DatabaseClient
from datamimic_ce.clients.mongodb_client import MongoDBClient
from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.constants.data_type_constants import DATA_TYPE_DICT, DATA_TYPE_LIST
from datamimic_ce.constants.element_constants import EL_GENERATE, EL_NESTED_KEY, EL_VARIABLE
from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.data_sources.weighted_entity_data_source import WeightedEntityDataSource
from datamimic_ce.enums.distribution_enums import SourceDistribution
from datamimic_ce.logger import logger
from datamimic_ce.model.constraints import SourceFileFormat, source_file_format, source_file_format_for
from datamimic_ce.services.source_script_evaluator import evaluate_source_template, interpolate_variables
from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.statements.nested_key_statement import NestedKeyStatement
from datamimic_ce.statements.reference_statement import ReferenceStatement
from datamimic_ce.statements.statement import Statement
from datamimic_ce.statements.statement_util import StatementUtil
from datamimic_ce.statements.variable_statement import VariableStatement
from datamimic_ce.utils.distribution_sampling import cumulated_index
from datamimic_ce.utils.file_content_storage import FileContentStorage
from datamimic_ce.utils.file_util import FileUtil
from datamimic_ce.utils.unique_sampling import unique_values


@dataclass(frozen=True)
class VariableSourcePlan:
    """Task-facing result of one centrally routed variable source."""

    kind: Literal["full_load", "iteration_selector", "iterator", "lazy", "storage", "weighted"]
    data: Iterable[Any] | None = None
    client: DatabaseClient | None = None
    weighted_source: WeightedEntityDataSource | None = None
    selector: str | None = None
    prefix: str = ""
    suffix: str = ""


class DataSourceRegistry:
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
            if isinstance(json_data, list):
                return json_data
            elif isinstance(json_data, dict):
                return [json_data]
            else:
                raise ValueError(f"JSON file '{key}' must contain a list of objects or a dictionary")
        elif source_format is SourceFileFormat.XML:
            return FileContentStorage.load_file_with_custom_func(
                key, lambda: xmltodict.parse(open(key).read(), attr_prefix="@", cdata_key="#text")
            )
        else:
            raise ValueError(f"Data source '{key}' is not supported is not handled by DataSourceRegistry")

    @staticmethod
    def data_source_cache_key(stmt: Statement) -> tuple[str | None, str | None]:
        """Cache key for a statement's data-source length. Statements may SHARE a name (e.g. three
        <iterate name='db_product'> feeding one table from different sources), so the key must
        include the source - keyed by name alone, the second statement inherits the first one's
        length and silently truncates its rows. A tuple key on real statement types, no string
        concatenation, no duck-typing."""
        if isinstance(stmt, GenerateStatement | VariableStatement | NestedKeyStatement):
            return (stmt.full_name, stmt.source)
        return (stmt.full_name, None)

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
        if not isinstance(stmt, GenerateStatement | VariableStatement | NestedKeyStatement):
            return

        root_ctx = ctx.root
        source_id: tuple[str | None, str | None] = DataSourceRegistry.data_source_cache_key(stmt)
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
            source_str = stmt.source
            if source_str is None:
                return
            # Try to evaluate script as source string
            # Ignore to check scripted source if eval failed in pre-execute task
            if source_str.startswith("{") and source_str.endswith("}"):
                try:
                    source_str = eval(source_str[1:-1])
                except:  # noqa: E722
                    return

            # 2: Get source info from ctx client (e.g. checking if it is SQL, MongoDB or CSV source)

            # Check if source is data source file or database collection/table.
            if isinstance(stmt, GenerateStatement):
                source_element = EL_GENERATE
            elif isinstance(stmt, VariableStatement):
                source_element = EL_VARIABLE
            elif isinstance(stmt, NestedKeyStatement):
                source_element = EL_NESTED_KEY
            else:
                return
            source_format = source_file_format_for(
                source_element,
                source_str,
                stmt.type,
            )
            # dbunit dataset: one table's row count (checked before the generic .xml branch below).
            if source_format is SourceFileFormat.DBUNIT_XML:
                ds_len = len(
                    FileUtil.read_dbunit_to_dict_list(
                        root_ctx.descriptor_dir / source_str, StatementUtil.resolve_source_entity(stmt)
                    )
                )
            # 2.1: Check if datasource is csv file
            elif source_format is not None:
                ds_len = len(
                    DataSourceRegistry._get_source(
                        str(root_ctx.descriptor_dir / source_str),
                        stmt.separator or ctx.root.default_separator,
                        source_format,
                    )
                )
            # 2.4: Check if datasource is memstore
            elif root_ctx.memstore_manager.contain(source_str):
                ds_len = root_ctx.memstore_manager.get_memstore(source_str).get_data_len_by_type(
                    StatementUtil.resolve_source_entity(stmt)
                )
            elif root_ctx.get_client_by_id(source_str) is not None:
                client = root_ctx.get_client_by_id(source_str)
                if client is None:
                    raise ValueError(
                        f"Client '{source_str}' could not be found in your context, please check your script"
                    )
                # handle database collection/table as data source
                from datamimic_ce.clients.rdbms_client import RdbmsClient

                selector = stmt.selector if isinstance(stmt, GenerateStatement | VariableStatement) else None
                iteration_selector = stmt.iteration_selector if isinstance(stmt, VariableStatement) else None

                if isinstance(client, RdbmsClient):
                    if selector is not None:
                        try:
                            ds_len = client.count_query_length(query=selector)
                        except ProgrammingError:
                            logger.error(
                                f"Cannot get length of database source '{source_str}' with selector '{selector}'"
                            )
                            return
                        except OperationalError:
                            logger.error(
                                f"Cannot get length of database source '{source_str}' with selector '{selector}'"
                            )
                            return
                    elif iteration_selector is not None:
                        try:
                            ds_len = client.count_query_length(query=iteration_selector)
                        except ProgrammingError:
                            logger.error(
                                f"Cannot get length of database source '{source_str}' "
                                f"with iterationSelector '{iteration_selector}'"
                            )
                            return
                        except OperationalError:
                            logger.error(
                                f"Cannot get length of database source '{source_str}' "
                                f"with iterationSelector '{iteration_selector}'"
                            )
                            return
                    elif stmt.source_entity is not None or stmt.type is not None:
                        ds_len = client.count_table_length(table_name=StatementUtil.resolve_source_entity(stmt))

                elif isinstance(client, MongoDBClient):
                    if selector is not None:
                        try:
                            ds_len = client.count_query_length(selector)
                        except ValueError:
                            return
                    elif (collection := StatementUtil.resolve_source_collection(stmt)) is not None:
                        try:
                            ds_len = client.count(collection_name=collection)
                        except ValueError:
                            return
                    elif iteration_selector is not None:
                        try:
                            ds_len = client.count_query_length(query=iteration_selector)
                        except ValueError:
                            logger.error(
                                f"Cannot get length of database source '{source_str}' "
                                f"with iterationSelector '{iteration_selector}'"
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

        # 3: Set length of data source. offset= shrinks the available window - the count
        # default and the count-above-source warning must both see the post-offset size.
        if isinstance(stmt, GenerateStatement) and stmt.offset:
            ds_len = max(0, ds_len - stmt.offset)
        root_ctx.data_source_len[source_id] = ds_len

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
            # Get shuffled data from datasource (local RNG; no global side-effect)
            shuffle_rng = Random(current_seed)
            shuffle_data = list(data)
            shuffle_rng.shuffle(shuffle_data)

            # Append shuffled data to result
            res.extend(shuffle_data)

            # Update current index and seed
            current_idx += source_len
            current_seed += 1

        start_idx_cap = start_idx % source_len
        return res[start_idx_cap : start_idx_cap + end_idx - start_idx]

    @staticmethod
    def get_distributed_data(
        data: Iterable,
        pagination: DataSourcePagination | None,
        cyclic: bool | None,
        seed: int,
        distribution: SourceDistribution,
    ) -> list:
        """Reorder loaded rows for a non-ORDERED distribution: RANDOM shuffles (permutation),
        CUMULATED selects with a bell-weighted index (with replacement). Single dispatch shared
        by <variable>, <generate> and <nestedKey>."""
        if distribution == SourceDistribution.CUMULATED:
            return DataSourceRegistry.get_cumulated_data(data, pagination, seed)  # cyclic n/a: never runs out
        return DataSourceRegistry.get_shuffled_data_with_cyclic(data, pagination, cyclic, seed)

    @staticmethod
    def get_unique_data(
        data: Iterable[Any], pagination: DataSourcePagination | None, seed: int, label: str
    ) -> list[Any]:
        """Select distinct rows without replacement: dedupe + shuffle, then return the page
        window. Sibling of get_cumulated_data; the unique counterpart of the random/cumulated
        selection. All pages share ``seed`` (stable per statement) -> one global deduped order ->
        each takes a disjoint window -> unique holds across pages. Strict: raises rather than
        silently under-generate when the window exceeds the distinct pool."""
        distinct = unique_values(data, Random(seed))
        if pagination is None:
            return distinct
        end = pagination.skip + pagination.limit
        if end > len(distinct):
            raise ValueError(
                f"Cannot generate {end} unique values for {label}: only {len(distinct)} distinct available"
            )
        return distinct[pagination.skip : end]

    @staticmethod
    def _variable_data_plan(
        context: SetupContext,
        stmt: VariableStatement,
        data: Iterable[Any] | None,
        pagination: DataSourcePagination | None,
        *,
        force_full_pool: bool,
    ) -> VariableSourcePlan:
        """Shape a routed variable pool and expose only an execution mode to the task."""
        if data is None:
            return VariableSourcePlan(kind="storage" if force_full_pool else "iterator")

        loads_all = stmt.distribution.loads_all or bool(stmt.unique)
        if not loads_all:
            return VariableSourcePlan(kind="storage" if force_full_pool else "iterator", data=data)

        seed = context.root.stable_distribution_seed(stmt.full_name)
        selected = (
            DataSourceRegistry.get_unique_data(
                data,
                None if force_full_pool else pagination,
                seed,
                f"<variable> '{stmt.name}'",
            )
            if stmt.unique
            else DataSourceRegistry.get_distributed_data(
                data,
                None if force_full_pool else pagination,
                stmt.cyclic,
                seed,
                stmt.distribution,
            )
        )
        return VariableSourcePlan(kind="storage" if force_full_pool else "full_load", data=selected)

    @staticmethod
    def get_cumulated_data(data: Iterable, pagination: DataSourcePagination | None, seed: int) -> list:
        """``distribution="cumulated"`` row selection: sample row indices with a
        bell shape (mean = middle of the load order) WITH replacement.

        Sibling of ``get_shuffled_data_with_cyclic`` (shuffle = permutation, no replacement).
        No ``cyclic`` parameter — with-replacement sampling never runs out, so wrap-around is
        meaningless.
        """
        rows = list(data)
        source_len = len(rows)
        if source_len == 0:
            return []

        if pagination is None:
            start_idx, end_idx = 0, source_len
        else:
            start_idx = pagination.skip
            end_idx = pagination.skip + pagination.limit
        span = end_idx - start_idx

        # One seeded RNG drives a single continuous draw sequence, so paginated batches
        # stay consistent (page 2 continues page 1). O(start_idx + span) draws;
        # fine for typical skips, revisit only if huge offsets show up.
        rng = Random(seed)
        picks = [rows[cumulated_index(rng, source_len - 1)] for _ in range(start_idx + span)]
        return picks[start_idx:]

    @staticmethod
    def load_csv_file(
        ctx: SetupContext,
        file_path: Path,
        separator: str,
        cyclic: bool | None,
        start_idx: int | None,
        end_idx: int | None,
        source_scripted: bool,
        prefix: str,
        suffix: str,
        offset: int = 0,
    ) -> list[dict]:
        """
        Load CSV content from file with skip and limit.

        :param ctx: SetupContext
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
        result = DataSourceRegistry.get_cyclic_data_list(
            data=file_data, cyclic=cyclic, pagination=pagination, offset=offset
        )

        # if sourceScripted then evaluate python expression in csv
        if source_scripted:
            evaluated_result = evaluate_source_template(ctx, result, prefix, suffix)
            return evaluated_result if isinstance(evaluated_result, list) else [evaluated_result]

        return result

    @staticmethod
    def load_generate_source(
        context: SetupContext | GenIterContext,
        stmt: GenerateStatement,
        source: str | None,
        separator: str,
        source_scripted: bool,
        start_idx: int | None,
        end_idx: int | None,
        pagination: DataSourcePagination | None,
    ) -> tuple[list[dict], bool]:
        """Load one generate source; this is the sole generate routing and paging owner."""
        build_from_source = True
        source_data: dict | list = []
        root = context.root
        prefix = stmt.variable_prefix or root.default_variable_prefix
        suffix = stmt.variable_suffix or root.default_variable_suffix

        if source is None:
            if stmt.script is None:
                build_from_source = False
            else:
                source_data = context.evaluate_python_expression(stmt.script)
        elif (
            source_file_format(source) is SourceFileFormat.WEIGHTED_CSV
            and not DataSourceRegistry._weighted_csv_has_header(root.descriptor_dir / source, separator)
        ):
            raise ValueError(
                f"<generate> '{stmt.full_name}': source '{source}' is a headerless weighted "
                "value|weight file - not supported at <generate>-level (only <key source=...> "
                "applies '.wgt.csv' weights today; add a header row to read it as a plain, "
                "unweighted CSV instead)"
            )
        elif (source_format := source_file_format_for(EL_GENERATE, source)) is SourceFileFormat.CSV:
            source_data = DataSourceRegistry.load_csv_file(
                ctx=root,
                file_path=root.descriptor_dir / source,
                separator=separator,
                cyclic=stmt.cyclic,
                start_idx=start_idx,
                end_idx=end_idx,
                source_scripted=source_scripted,
                prefix=prefix,
                suffix=suffix,
                offset=stmt.offset,
            )
        elif source_format is SourceFileFormat.JSON:
            source_data = DataSourceRegistry.load_json_file(
                root.descriptor_dir / source, stmt.cyclic, start_idx, end_idx, offset=stmt.offset
            )
            if source_scripted:
                try:
                    source_data = evaluate_source_template(root, source_data, prefix, suffix)
                except Exception as error:
                    logger.debug(f"Failed to pre-evaluate source script for {stmt.full_name}: {error}")
        elif source_format is SourceFileFormat.XLSX:
            source_data = DataSourceRegistry.load_xlsx_file(
                root.descriptor_dir / source, stmt.cyclic, start_idx, end_idx, offset=stmt.offset
            )
        elif source_format is SourceFileFormat.FIXED_WIDTH:
            source_data = DataSourceRegistry.load_fixed_width_file(
                root.descriptor_dir / source, stmt.cyclic, start_idx, end_idx, offset=stmt.offset
            )
        elif source_format is SourceFileFormat.DBUNIT_XML:
            source_data = FileUtil.read_dbunit_to_dict_list(
                root.descriptor_dir / source, StatementUtil.resolve_source_entity(stmt)
            )
            if stmt.offset:
                source_data = source_data[stmt.offset :]
        elif source_format is SourceFileFormat.XML:
            source_data = DataSourceRegistry.load_xml_file(
                root.descriptor_dir / source, stmt.cyclic, start_idx, end_idx, offset=stmt.offset
            )
            if source_scripted:
                source_data = evaluate_source_template(context, source_data, prefix, suffix)
        elif root.memstore_manager.contain(source):
            if stmt.offset:
                raise ValueError(
                    f"<generate> '{stmt.full_name}': offset= is only supported for file sources, "
                    f"not memstore '{source}'"
                )
            source_data = root.memstore_manager.get_memstore(source).get_data_by_type(
                StatementUtil.resolve_source_entity(stmt), pagination, stmt.cyclic
            )
        elif root.clients.get(source) is not None:
            if stmt.offset:
                raise ValueError(
                    f"<generate> '{stmt.full_name}': offset= is only supported for file sources, "
                    f"not database client '{source}' - use a selector with an SQL/Mongo skip instead"
                )
            client = root.clients[source]
            selector = interpolate_variables(root, stmt.selector or "", prefix, suffix)
            if isinstance(client, MongoDBClient):
                if stmt.selector:
                    source_data = client.get_by_page_with_query(query=selector, pagination=pagination)
                elif (collection := StatementUtil.resolve_source_collection(stmt)) is not None:
                    source_data = client.get_by_page_with_type(collection_name=collection, pagination=pagination)
                else:
                    raise ValueError(
                        "MongoDB source requires at least attribute 'sourceEntity', 'type', 'selector' "
                        "or 'iterationSelector'"
                    )
                if not source_data and stmt.contain_mongodb_upsert(root):
                    source_data = [{}]
            elif isinstance(client, RdbmsClient):
                if stmt.selector:
                    source_data = client.get_by_page_with_query(original_query=selector, pagination=pagination)
                else:
                    source_data = client.get_by_page_with_type(
                        table_name=StatementUtil.resolve_source_entity(stmt), pagination=pagination
                    )
            else:
                raise ValueError(f"Cannot load data from client: {type(client).__name__}")
        else:
            raise ValueError(f"cannot find data source {source} for iterate task")

        rows = source_data if isinstance(source_data, list) else [source_data]
        return rows, build_from_source

    @staticmethod
    def plan_variable_source(
        context: SetupContext,
        stmt: VariableStatement,
        pagination: DataSourcePagination | None,
        *,
        force_full_pool: bool,
    ) -> VariableSourcePlan:
        """Route and page a variable source without leaking source policy into its task."""
        source = stmt.source
        if source is None:
            raise ValueError(f"<variable> '{stmt.name}' has no source to plan")

        loads_all = stmt.distribution.loads_all or bool(stmt.unique)
        source_format = source_file_format_for(EL_VARIABLE, source)
        separator = stmt.separator or context.default_separator

        if source_format is SourceFileFormat.WEIGHTED_ENTITY_CSV:
            seeded = context.derive_seeded_rng()
            return VariableSourcePlan(
                kind="weighted",
                weighted_source=WeightedEntityDataSource(
                    file_path=context.root.descriptor_dir / source,
                    separator=separator,
                    rng=seeded if seeded is not None else Random(),
                    weight_column_name=stmt.weight_column,
                ),
            )

        if stmt.selector is not None or stmt.iteration_selector is not None:
            selector = stmt.selector or stmt.iteration_selector
            if selector is None:  # narrowed explicitly for static analysis
                raise RuntimeError("variable selector plan reached an impossible empty selector")
            prefix = stmt.variable_prefix or context.default_variable_prefix
            suffix = stmt.variable_suffix or context.default_variable_suffix
            client = context.get_client_by_id(source)
            if not isinstance(client, DatabaseClient):
                raise ValueError(
                    f"<variable> '{stmt.name}': 'selector' only works with 'source' database (MongoDB, SQL)"
                )
            if stmt.iteration_selector is not None:
                return VariableSourcePlan(
                    kind="iteration_selector",
                    client=client,
                    selector=selector,
                    prefix=prefix,
                    suffix=suffix,
                )

            rendered_selector = interpolate_variables(context, selector, prefix, suffix)
            if loads_all or force_full_pool or stmt.is_global_variable:
                data = client.get_by_page_with_query(rendered_selector)
            else:
                length = context.data_source_len.get(DataSourceRegistry.data_source_cache_key(stmt))
                if length is None:
                    length = client.count_query_length(rendered_selector)
                data = client.get_cyclic_data(rendered_selector, bool(stmt.cyclic), length, pagination)
            return DataSourceRegistry._variable_data_plan(
                context, stmt, data, pagination, force_full_pool=force_full_pool
            )

        if source_format is not None:
            if source_format is SourceFileFormat.CSV:
                data = FileUtil.read_csv_to_dict_list(context.root.descriptor_dir / source, separator)
            elif source_format is SourceFileFormat.XLSX:
                data = FileUtil.read_xlsx_to_dict_list(context.root.descriptor_dir / source)
            elif source_format is SourceFileFormat.FIXED_WIDTH:
                data = FileUtil.read_fixed_width_to_dict_list(context.root.descriptor_dir / source)
            elif source_format is SourceFileFormat.JSON:
                data = FileUtil.read_json_to_list(context.root.descriptor_dir / source)
            else:
                raise ValueError(f"Unsupported <variable> source format: {source_format.value}")
            if not (loads_all or force_full_pool):
                data = DataSourceRegistry.get_cyclic_data_iterator(data, pagination, stmt.cyclic)
            return DataSourceRegistry._variable_data_plan(
                context, stmt, data, pagination, force_full_pool=force_full_pool
            )

        client = context.get_client_by_id(source)
        if client is not None:
            if not isinstance(client, DatabaseClient):
                raise ValueError(f"Cannot get data from source '{source}' of <variable> '{stmt.name}'")
            product_type = StatementUtil.resolve_source_entity(stmt)
            if product_type is None:
                data = None
            elif loads_all or force_full_pool:
                data = client.get_by_page_with_type(product_type)
            elif stmt.cyclic:
                data = DataSourceRegistry.get_cyclic_data_list(
                    client.get_by_page_with_type(product_type), pagination, cyclic=True
                )
            else:
                data = client.get_by_page_with_type(product_type, pagination)
            return DataSourceRegistry._variable_data_plan(
                context, stmt, data, pagination, force_full_pool=force_full_pool
            )

        if context.memstore_manager.contain(source):
            product_type = StatementUtil.resolve_source_entity(stmt)
            memstore = context.memstore_manager.get_memstore(source)
            data = (
                memstore.get_all_data_by_type(product_type)
                if loads_all or force_full_pool
                else memstore.get_data_by_type(product_type, pagination, stmt.cyclic)
            )
            return DataSourceRegistry._variable_data_plan(
                context, stmt, data, pagination, force_full_pool=force_full_pool
            )

        if force_full_pool:
            raise ValueError(
                f"<variable> '{stmt.name}': 'storage' is not supported for a "
                "dynamic/script-evaluated source (no stable pool to materialize up front)"
            )
        return VariableSourcePlan(kind="lazy")

    @staticmethod
    def load_variable_iteration_selector(
        context: Context,
        client: DatabaseClient,
        selector: str,
        prefix: str,
        suffix: str,
    ) -> Iterable[Any]:
        """Evaluate and execute one row-dependent variable selector."""
        return client.get_by_page_with_query(interpolate_variables(context, selector, prefix, suffix))

    @staticmethod
    def load_variable_lazy_source(
        context: Context,
        stmt: VariableStatement,
        pagination: DataSourcePagination | None,
    ) -> Iterator[Any] | None:
        """Evaluate a dynamic variable source and apply its paging/distribution contract."""
        if stmt.source is None:
            return None
        data = context.evaluate_python_expression(stmt.source)
        if stmt.distribution.loads_all or stmt.unique:
            seed = context.root.stable_distribution_seed(stmt.full_name)
            selected = (
                DataSourceRegistry.get_unique_data(data, pagination, seed, f"<variable> '{stmt.name}'")
                if stmt.unique
                else DataSourceRegistry.get_distributed_data(data, pagination, stmt.cyclic, seed, stmt.distribution)
            )
            return iter(selected)
        return DataSourceRegistry.get_cyclic_data_iterator(data, pagination, stmt.cyclic)

    @staticmethod
    def load_nested_key_source(context: Context, stmt: NestedKeyStatement) -> list[Any] | dict[str, Any]:
        """Resolve and load the raw source owned by one nested key."""
        source_expression = stmt.source
        if source_expression is None:
            raise ValueError(f"<nestedKey> '{stmt.name}' has no source to load")
        source = (
            context.evaluate_python_expression(source_expression[1:-1])
            if source_expression.startswith("{") and source_expression.endswith("}")
            else source_expression
        )
        if not isinstance(source, str):
            raise ValueError(f"Source expression of <nestedKey> '{stmt.name}' must evaluate to a string")

        source_format = source_file_format_for(EL_NESTED_KEY, source, stmt.type)
        if stmt.type == DATA_TYPE_LIST:
            if source_format is SourceFileFormat.CSV:
                separator = stmt.separator or context.root.default_separator
                return FileUtil.read_csv_to_dict_list(context.root.descriptor_dir / source, separator)
            if source_format is SourceFileFormat.JSON:
                return FileUtil.read_json_to_list(context.root.descriptor_dir / source)
            if context.root.memstore_manager.contain(source):
                return context.root.memstore_manager.get_memstore(source).get_data_by_type(
                    StatementUtil.resolve_source_entity(stmt), None, stmt.cyclic
                )
            raise ValueError(f"Invalid source '{source}' of nestedkey '{stmt.name}'")

        if stmt.type == DATA_TYPE_DICT:
            if source_format is SourceFileFormat.JSON:
                return FileUtil.read_json_to_dict(context.root.descriptor_dir / source)
            raise ValueError(f"Source of nestedkey having type as 'dict' does not support format {source}")

        if context.root.memstore_manager.contain(source):
            return context.root.memstore_manager.get_memstore(source).get_data_by_type(
                StatementUtil.resolve_source_entity(stmt), None, stmt.cyclic
            )
        raise ValueError(f"Cannot load data from source '{source_expression}' of <nestedKey> '{stmt.name}'")

    @staticmethod
    def finalize_nested_key_source(
        context: Context,
        stmt: NestedKeyStatement,
        data: list[Any] | dict[str, Any],
    ) -> list[Any] | dict[str, Any]:
        """Apply nested-key source templating and distribution in one boundary owner."""
        source_scripted = (
            stmt.source_script if stmt.source_script is not None else bool(context.root.default_source_scripted)
        )
        result: list[Any] | dict[str, Any] = data
        if source_scripted:
            prefix = stmt.variable_prefix or context.root.default_variable_prefix
            suffix = stmt.variable_suffix or context.root.default_variable_suffix
            evaluated = evaluate_source_template(context, result, prefix, suffix)
            if not isinstance(evaluated, list | dict):
                raise ValueError(f"Source template of <nestedKey> '{stmt.name}' must evaluate to list or dict")
            result = evaluated
        if isinstance(result, list) and stmt.distribution.loads_all:
            seed = context.root.get_distribution_seed()
            result = DataSourceRegistry.get_distributed_data(result, None, stmt.cyclic, seed, stmt.distribution)
        return result

    @staticmethod
    def window_nested_key_rows(data: list[Any], count: int | None, cyclic: bool | None) -> list[Any]:
        """Return the nested-key execution window; paging and wrap policy stay in the registry."""
        size = len(data) if count is None else count if cyclic else min(count, len(data))
        return DataSourceRegistry.get_cyclic_data_list(
            data=data,
            pagination=DataSourcePagination(0, size),
            cyclic=bool(cyclic),
        )

    @staticmethod
    def reference_uses_shared_cycle(stmt: ReferenceStatement) -> bool:
        """Whether an unpaged reference needs root-owned rotation across rebuilt tasks."""
        if stmt.cyclic:
            return True
        return stmt.distribution is not None and SourceDistribution.coerce(stmt.distribution) is not (
            SourceDistribution.RANDOM
        )

    @staticmethod
    def load_reference_source(
        context: Context,
        stmt: ReferenceStatement,
        pagination: DataSourcePagination | None,
    ) -> list[dict[str, Any]]:
        """Load, map and select reference rows behind one typed datasource boundary."""
        client = context.root.clients.get(stmt.source)
        if not isinstance(client, RdbmsClient | MongoDBClient):
            raise ValueError(
                f"<reference> '{stmt.name}': source '{stmt.source}' is not a "
                "<database> or <mongodb> client (RDBMS and MongoDB are supported)"
            )
        rows = client.get_random_rows_by_columns(stmt.source_type, stmt.source_keys)
        if not rows:
            raise ValueError(f"No data found for reference {stmt.name}")
        records = [dict(zip(stmt.targets, row, strict=True)) for row in rows]

        seed = context.root.stable_distribution_seed(stmt.full_name)
        if stmt.unique:
            return DataSourceRegistry.get_unique_data(records, pagination, seed, f"<reference> '{stmt.name}'")

        distribution = SourceDistribution.coerce(stmt.distribution)
        if (stmt.distribution is not None and distribution is not SourceDistribution.RANDOM) or stmt.cyclic:
            if distribution is SourceDistribution.ORDERED or (stmt.distribution is None and stmt.cyclic):
                return DataSourceRegistry._ordered_reference_rows(records, stmt, pagination)
            return DataSourceRegistry.get_distributed_data(records, pagination, stmt.cyclic, seed, distribution)

        size = pagination.limit if pagination is not None else 1
        return [context.rng.choice(records) for _ in range(size)]

    @staticmethod
    def _ordered_reference_rows(
        records: list[dict[str, Any]],
        stmt: ReferenceStatement,
        pagination: DataSourcePagination | None,
    ) -> list[dict[str, Any]]:
        if pagination is None:
            return records
        start = pagination.skip
        size = pagination.limit
        if stmt.cyclic:
            return [records[(start + index) % len(records)] for index in range(size)]
        if start + size > len(records):
            raise ValueError(
                f"<reference> '{stmt.name}' distribution='ordered' needs {start + size} rows "
                f'but the source has only {len(records)} (use cyclic="true" to wrap around)'
            )
        return records[start : start + size]

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
        file_data = DataSourceRegistry._get_source(str(file_path), ",", SourceFileFormat.XML)
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
