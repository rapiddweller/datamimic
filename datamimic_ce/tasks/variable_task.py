# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import inspect
from collections.abc import Iterator
from random import Random
from typing import Any, Final

from datamimic_ce.clients.database_client import DatabaseClient
from datamimic_ce.constants.attribute_constants import (
    ATTR_CONSTANT,
    ATTR_ENTITY,
    ATTR_GENERATOR,
    ATTR_SCRIPT,
    ATTR_SOURCE,
    ATTR_TYPE,
    ATTR_VALUES,
)
from datamimic_ce.constants.element_constants import EL_VARIABLE
from datamimic_ce.contexts.context import Context, DotableDict
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.data_sources.data_source_registry import DataSourceRegistry
from datamimic_ce.data_sources.weighted_entity_data_source import WeightedEntityDataSource
from datamimic_ce.logger import logger
from datamimic_ce.model.constraints import SourceFileFormat, source_file_format_for
from datamimic_ce.statements.statement_util import StatementUtil
from datamimic_ce.statements.variable_statement import VariableStatement
from datamimic_ce.tasks.key_variable_task import KeyVariableTask
from datamimic_ce.tasks.task import CommonSubTask
from datamimic_ce.tasks.task_util import TaskUtil
from datamimic_ce.tasks.variable_iterator import VariableIterator
from datamimic_ce.utils.domain_class_util import DomainClassUtil
from datamimic_ce.utils.file_util import FileUtil
from datamimic_ce.utils.string_util import StringUtil


def _constructor_params(cls: type) -> frozenset[str]:
    """Names accepted by ``cls.__init__`` — used to inject only supported kwargs."""
    try:
        return frozenset(inspect.signature(cls).parameters)
    except (TypeError, ValueError):
        return frozenset()


class VariableTask(KeyVariableTask, CommonSubTask):
    _iterator: Iterator[Any] | None
    _ITERATOR_MODE: Final = "iterator"
    _ENTITY_MODE: Final = "entity_builder"
    _WEIGHTED_ENTITY_MODE: Final = "weighted_entity"
    _ITERATION_SELECTOR_MODE: Final = "iteration_selector"
    _FULL_LOAD_MODE: Final = "full_load"
    _LAZY_ITERATOR_MODE: Final = "lazy_iterator"
    _STORAGE_MODE: Final = "storage"

    def __init__(
        self,
        ctx: SetupContext,
        statement: VariableStatement,
        pagination: DataSourcePagination | None,
    ):
        super().__init__(ctx, statement, pagination)
        self._source_script = (
            statement.source_script if statement.source_script is not None else bool(ctx.default_source_scripted)
        )
        self._statement: VariableStatement = statement
        descriptor_dir = ctx.root.descriptor_dir
        # Always bound: _finalize_pool's non-storage tail now handles every branch (including
        # "ordered", which never reads seed) with one shared call, so seed must be a valid
        # argument even on the path that doesn't use it - real UnboundLocalError caught by the
        # regression suite the first time this was written as a bare `seed: int` annotation.
        seed: int = 0
        file_data: list[dict[str, Any]] | None = None
        self._full_load_iterator = None

        # storage="value"/"data"/"iterator" exposes a materialized source pool instead of the
        # default per-execute()-advancing scalar (see VariableIterator's docstring for the
        # "iterator" contract). VariableModel already rejects storage combined with
        # iterationSelector, a weighted-entity source, or no source= at all - the two remaining
        # combinations that need runtime state to detect (not decidable from raw XML attributes
        # alone) are checked here.
        self._storage_mode = statement.storage
        if self._storage_mode is not None:
            if statement.is_global_variable:
                raise ValueError(
                    f"<variable> '{statement.name}': 'storage' is not supported on a global "
                    "(setup-scope) variable - it has no per-row position to expose."
                )
            if self._source_script:
                raise ValueError(
                    f"<variable> '{statement.name}': 'storage' cannot be combined with sourceScripted "
                    "(not meaningful for a list/proxy value)"
                )
            if statement.converter is not None:
                raise ValueError(
                    f"<variable> '{statement.name}': 'storage' cannot be combined with 'converter' "
                    "(not meaningful for a list/proxy value)"
                )
        # Only ORDERED paginates sequentially; RANDOM and CUMULATED load all rows.
        # unique also needs the whole pool (dedupe + sample without replacement).
        loads_all = self.statement.distribution.loads_all or bool(self.statement.unique)
        # storage= always needs the full pool materialized once, regardless of distribution's
        # normal per-page pagination (pageSize is ignored) - independent of whether loads_all
        # already implies a full read for this distribution.
        force_full_pool = self._storage_mode is not None
        if loads_all or force_full_pool:
            # Stable per-statement seed so random / cumulated / unique stay consistent across pages
            # (and, for storage=, across the one-time full-pool materialization).
            seed = ctx.root.stable_distribution_seed(self.statement.full_name)

        # Try to init generation mode of VariableTask
        if statement.source is not None:
            source_str = statement.source
            source_format = source_file_format_for(EL_VARIABLE, source_str)
            separator = statement.separator or ctx.default_separator
            # Load data from weighted entity file
            if source_format is SourceFileFormat.WEIGHTED_ENTITY_CSV:
                seeded = ctx.derive_seeded_rng()
                self._weighted_data_source = WeightedEntityDataSource(
                    file_path=descriptor_dir / source_str,
                    separator=separator,
                    rng=seeded if seeded is not None else Random(),
                    weight_column_name=statement.weight_column,
                )
                self._mode = self._WEIGHTED_ENTITY_MODE
            # Create datasource if statement has property "selector" or "iterationSelector"
            # (working with datasource database)
            elif statement.selector is not None or statement.iteration_selector is not None:
                # set selector and prefix, suffix
                self._selector = statement.selector or statement.iteration_selector
                self._prefix = statement.variable_prefix or ctx.default_variable_prefix
                self._suffix = statement.variable_suffix or ctx.default_variable_suffix

                # Get client (Database)
                client = ctx.get_client_by_id(source_str)
                if not isinstance(client, DatabaseClient):
                    raise ValueError(
                        f"<variable> '{self._statement.name}': 'selector' only works with 'source' database (MongoDB, "
                        f"SQL)"
                    )
                # Handle iteration selector
                if statement.iteration_selector is not None:
                    self._client = client
                    self._mode = self._ITERATION_SELECTOR_MODE
                # Handle static selector
                else:
                    # Evaluate script selector
                    if self._selector is None:
                        raise ValueError("No selector value in statement: {self._statement.name}")
                    selector = TaskUtil.evaluate_variable_concat_prefix_suffix(
                        context=ctx,
                        expr=self._selector,
                        prefix=self._prefix,
                        suffix=self._suffix,
                    )
                    # Select data from database and shuffle
                    if loads_all or force_full_pool:
                        selected_data = client.get_by_page_with_query(selector)
                        self._finalize_pool(selected_data, loads_all, seed)
                    else:
                        # global variable (setup variable, out of generate_stmt scope) don't need pagination and cyclic
                        if self._statement.is_global_variable:
                            file_data = client.get_by_page_with_query(selector)
                        # Get data source with pagination
                        else:
                            len_data = ctx.data_source_len.get(DataSourceRegistry.data_source_cache_key(statement))
                            if len_data is None:
                                len_data = client.count_query_length(selector)
                            file_data = client.get_cyclic_data(
                                selector,
                                statement.cyclic or False,
                                len_data,
                                pagination,
                            )
                        self._iterator = iter(file_data) if file_data is not None else None
                        self._mode = self._ITERATOR_MODE
            else:
                # Load data from csv or json file
                if source_format is not None:
                    if source_format is SourceFileFormat.CSV:
                        loaded_file_data = FileUtil.read_csv_to_dict_list(
                            file_path=descriptor_dir / source_str, separator=separator
                        )
                    elif source_format is SourceFileFormat.XLSX:
                        loaded_file_data = FileUtil.read_xlsx_to_dict_list(descriptor_dir / source_str)
                    elif source_format is SourceFileFormat.FIXED_WIDTH:
                        loaded_file_data = FileUtil.read_fixed_width_to_dict_list(descriptor_dir / source_str)
                    else:
                        loaded_file_data = FileUtil.read_json_to_list(descriptor_dir / source_str)
                    if loads_all or force_full_pool:
                        self._finalize_pool(loaded_file_data, loads_all, seed)
                    else:
                        self._iterator = DataSourceRegistry.get_cyclic_data_iterator(
                            data=loaded_file_data,
                            cyclic=statement.cyclic,
                            pagination=pagination,
                        )
                        self._mode = self._ITERATOR_MODE
                # Load data from source without selector
                else:
                    is_lazy_source = False
                    # Get data from database
                    if ctx.get_client_by_id(source_str):
                        client = ctx.get_client_by_id(source_str)
                        if not isinstance(client, DatabaseClient):
                            raise ValueError(
                                f"Cannot get data from source '{source_str}' of <variable> '{statement.name}'"
                            ) from None

                        # in case of dbms product_type reflects the table name (sourceEntity -> type -> name)
                        product_type = StatementUtil.resolve_source_entity(statement)
                        # loads_all (random/cumulated) needs the WHOLE table to sample/shuffle from -
                        # passing pagination here would hand _distributed_iter just one page and
                        # silently truncate output to a page's worth of rows (reproduced: pageSize=5,
                        # count=20 produced only 5 rows).
                        if product_type is None:
                            file_data = None
                        elif loads_all or force_full_pool:
                            # storage= (force_full_pool) needs the raw full pool, not a page
                            # window - and NOT run through get_cyclic_data_list's page-length
                            # pre-extension below (that would double-apply the wrap on top of
                            # VariableIterator's own position % len(pool) modulo).
                            file_data = client.get_by_page_with_type(product_type)
                        elif statement.cyclic:
                            # cyclic=true on distribution="ordered" needs to know the WHOLE pool to
                            # wrap correctly - a DB-side skip/limit window just returns short
                            # (reproduced: pool=7, count=11 -> only 7 rows, no wrap) since neither
                            # get_by_page_with_type nor a plain iter() over its result knows how to
                            # cycle. Mirrors what the memstore branch below already gets right
                            # (memstore.get_data_by_type -> DataSourceRegistry.get_cyclic_data_list,
                            # which also needs the full list) - same trade-off, same shared helper.
                            file_data = DataSourceRegistry.get_cyclic_data_list(
                                client.get_by_page_with_type(product_type), pagination, cyclic=True
                            )
                        else:
                            file_data = client.get_by_page_with_type(product_type, pagination)
                    # Get data from memstore
                    elif ctx.memstore_manager.contain(source_str):
                        product_type = StatementUtil.resolve_source_entity(statement)
                        memstore = ctx.memstore_manager.get_memstore(source_str)
                        file_data = (
                            memstore.get_all_data_by_type(product_type)
                            if (loads_all or force_full_pool)
                            else memstore.get_data_by_type(product_type, pagination, statement.cyclic)
                        )
                    # Get data from script in lazy mode
                    else:
                        is_lazy_source = True

                    if is_lazy_source:
                        if force_full_pool:
                            raise ValueError(
                                f"<variable> '{statement.name}': 'storage' is not supported for a "
                                "dynamic/script-evaluated source (no stable pool to materialize up front)"
                            )
                        self._iterator = None
                        self._mode = self._LAZY_ITERATOR_MODE
                    else:
                        self._finalize_pool(file_data, loads_all, seed)
        elif statement.entity is not None:
            # Create entity builder
            locale = statement.locale or ctx.default_locale
            dataset = statement.dataset or ctx.default_dataset
            try:
                self._entity_generator = self._get_entity_generator(
                    ctx,
                    entity_name=statement.entity,
                    locale=locale,
                    dataset=dataset,
                    count=1 if pagination is None else pagination.limit,
                    statement=statement,
                )
            except Exception as e:
                logger.error(
                    f"Failed to execute <variable> '{self._statement.name}': "
                    f"Can't create entity '{statement.entity}': {e}"
                )
                #  Avoid printing tracebacks directly; structured logs handle context.
                raise ValueError(
                    f"Failed to execute <variable> '{self._statement.name}': "
                    f"Can't create entity '{statement.entity}': {e}"
                ) from e

            self._mode = self._ENTITY_MODE
        else:
            self._determine_generation_mode(ctx)

        if self._mode is None:
            raise ValueError(
                f"Must specify at least one attribute for element <{EL_VARIABLE}> '{self._statement.name}',"
                f" such as '{ATTR_SCRIPT}', '{ATTR_CONSTANT}', '{ATTR_VALUES}', "
                f"'{ATTR_GENERATOR}', '{ATTR_SOURCE}, '{ATTR_ENTITY}' or '{ATTR_TYPE}'"
            )

    @property
    def statement(self) -> VariableStatement:
        return self._statement

    @staticmethod
    def _get_entity_generator(
        ctx: Context, entity_name: str, locale: str, dataset: str, count: int, statement: VariableStatement
    ):
        from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
        from datamimic_ce.domains.domain_core.runtime import spawn_rng

        entity_class_name, kwargs = StringUtil.parse_constructor_string(entity_name)
        # Inject dataset if not explicitly provided in constructor
        kwargs.setdefault("dataset", dataset)
        demographic_context = ctx.root.demographic_context
        # Build demographic config + rng from statement attributes when present
        demo_cfg = None
        if any(
            v is not None
            for v in (statement.age_min, statement.age_max, statement.conditions_include, statement.conditions_exclude)
        ):
            includes = (
                frozenset(x.strip() for x in (statement.conditions_include or "").split(",") if x.strip())
                if statement.conditions_include is not None
                else None
            )
            excludes = (
                frozenset(x.strip() for x in (statement.conditions_exclude or "").split(",") if x.strip())
                if statement.conditions_exclude is not None
                else None
            )
            demo_cfg = DemographicConfig(
                age_min=statement.age_min,
                age_max=statement.age_max,
                conditions_include=includes,
                conditions_exclude=excludes,
            )
        rng_obj = Random(statement.rng_seed) if statement.rng_seed is not None else None
        if demo_cfg is None and demographic_context is not None and demographic_context.overrides is not None:
            # Share profile-level defaults when no per-variable overrides are provided.
            demo_cfg = demographic_context.overrides
        if rng_obj is None and demographic_context is not None:
            # Derive entity-level RNGs from the demographics root seed to keep sampling reproducible.
            rng_obj = spawn_rng(demographic_context.rng)
        if rng_obj is None:
            # Fall back to the model-wide <setup rngSeed> root; None if no seed was given.
            rng_obj = ctx.root.derive_seeded_rng()
        demographic_sampler = demographic_context.sampler if demographic_context is not None else None
        # Build from the last parsed VariableTask (self is not accessible in staticmethod); use closure via locals()

        # Resolve the service class by name through the entity registry
        # (auto-discovered). Fall back to an explicit dotted module path such
        # as "common.models.Company" for callers that bypass the registry.
        from datamimic_ce.domains.domain_core.entity_registry import get_entity_service_class

        entity_cls = get_entity_service_class(entity_class_name)
        if entity_cls is None:
            if "." in entity_class_name:
                return DomainClassUtil.create_instance(f"datamimic_ce.domains.{entity_class_name}", **kwargs)
            raise ValueError(f"Entity '{entity_name}' is not supported in the domain architecture.")

        # Only inject the optional demographic/rng knobs the constructor accepts —
        # determined from the signature, not a hand-maintained per-entity list.
        accepted = _constructor_params(entity_cls)
        if demo_cfg is not None and "demographic_config" in accepted:
            kwargs.setdefault("demographic_config", demo_cfg)
        if demographic_sampler is not None and "demographic_sampler" in accepted:
            kwargs.setdefault("demographic_sampler", demographic_sampler)
        if rng_obj is not None and "rng" in accepted:
            kwargs["rng"] = rng_obj
        return entity_cls(**kwargs)

    def _distributed_iter(self, data, pagination, seed):
        """Iterator over loaded rows for the load-all selections: random shuffle /
        cumulated bell / unique (distinct, no replacement). All page-window slicing lives
        in the registry, so unique stays multiprocessing-safe. Consumed via ``_full_load_iterator``."""
        if self._statement.unique:
            return iter(
                DataSourceRegistry.get_unique_data(data, pagination, seed, f"<variable> '{self._statement.name}'")
            )
        return iter(
            DataSourceRegistry.get_distributed_data(
                data, pagination, self._statement.cyclic, seed, self._statement.distribution
            )
        )

    def _storage_pool(self, data, seed) -> list:
        """storage= counterpart of ``_distributed_iter``: same shaping (shuffle/cumulated/unique),
        but the RAW, unwindowed full pool (pagination=None) - VariableIterator's own
        ``position % len(pool)`` handles cyclic wrap at read time, so pre-extending the list here
        (like the page-windowed ``_distributed_iter`` path does for a paginated page) would
        double-apply the wrap."""
        if self._statement.unique:
            return DataSourceRegistry.get_unique_data(data, None, seed, f"<variable> '{self._statement.name}'")
        return DataSourceRegistry.get_distributed_data(
            data, None, self._statement.cyclic, seed, self._statement.distribution
        )

    def _finalize_pool(self, data, loads_all: bool, seed) -> None:
        """Shared tail once a branch has produced its pool (``data``, still page-windowed unless
        storage= forced a full read). Normal variables dispatch to the existing per-execute()
        iterator/full_load behavior; storage= variables materialize ``self._data_list`` once
        instead and switch to ``_STORAGE_MODE``. ``loads_all`` decides whether shaping
        (_distributed_iter/_storage_pool) is needed - independent of whether storage= forced the
        LOAD itself to ignore pagination (a storage= variable on an "ordered" distribution still
        needs no shuffling, just the raw full list in load order)."""
        if self._storage_mode is not None:
            if data is None:
                self._data_list = []
            elif loads_all:
                self._data_list = self._storage_pool(data, seed)
            else:
                self._data_list = list(data)
            if self._storage_mode == "data":
                self._data_list = [DotableDict(row) if isinstance(row, dict) else row for row in self._data_list]
            self._storage_row_counter = 0
            self._mode = self._STORAGE_MODE
            return
        if loads_all:
            self._full_load_iterator = (
                self._distributed_iter(data, self._pagination, seed) if data is not None else None
            )
            self._mode = self._FULL_LOAD_MODE
        else:
            self._iterator = iter(data) if data is not None else None
            self._mode = self._ITERATOR_MODE

    def _compute_storage_value(self):
        """storage="data": the same materialized pool every generated row. storage="value": the
        pool's first row, fixed, every generated row - a distinct behavior from the unset default
        (which advances one row per execute() call), matching DATAMIMIC EE's contract exactly.
        storage="iterator": a VariableIterator bound to this row's GLOBAL position
        (self._pagination.skip is the page's true global row offset - see generate_worker.py's
        per-page pagination construction - plus a per-task counter incremented once per
        execute() call, which naturally resets every page since VariableTask is rebuilt fresh per
        page). This gives correct SP==MP determinism for free: worker 2's page continues the
        cyclic sequence exactly where worker 1's left off."""
        if self._storage_mode == "data":
            return self._data_list
        if self._storage_mode == "value":
            return self._data_list[0] if self._data_list else None
        skip = self._pagination.skip if self._pagination is not None else 0
        position = skip + self._storage_row_counter
        self._storage_row_counter += 1
        return VariableIterator(self._data_list, bool(self._statement.cyclic), position)

    def execute(self, ctx: Context) -> None:
        """
        Generate data for element <variable>
        """

        if self._mode == self._ITERATOR_MODE:
            value = next(self._iterator) if self._iterator is not None else None
        elif self._mode == self._ENTITY_MODE:
            value = self._entity_generator.generate()
        elif self._mode == self._WEIGHTED_ENTITY_MODE:
            value = self._weighted_data_source.generate()
        elif self._mode == self._ITERATION_SELECTOR_MODE:
            if self._selector is None:
                raise ValueError(f"No selector value in statement: {self._statement.name}")
            selector = TaskUtil.evaluate_variable_concat_prefix_suffix(
                context=ctx,
                expr=self._selector,
                prefix=self._prefix,
                suffix=self._suffix,
            )
            value = self._client.get_by_page_with_query(selector)
        elif self._mode == self._FULL_LOAD_MODE:
            if self._full_load_iterator is None:
                raise StopIteration(f"No more rows to iterate for statement: {self._statement.name}")
            value = next(self._full_load_iterator)
        elif self._mode == self._STORAGE_MODE:
            value = self._compute_storage_value()
        elif self._mode == self._LAZY_ITERATOR_MODE:
            if isinstance(self._statement, VariableStatement):
                loads_all = self._statement.distribution.loads_all
            else:
                loads_all = False
            if self._statement.source is None:
                return None
            file_data = ctx.evaluate_python_expression(self._statement.source)
            if loads_all:
                # Stable per-statement seed (like __init__ above) so a paginated script source stays
                # consistent across pages for random / cumulated / unique.
                self._full_load_iterator = self._distributed_iter(
                    file_data, self._pagination, ctx.root.stable_distribution_seed(self._statement.full_name)
                )
                self._mode = self._FULL_LOAD_MODE
                if self._full_load_iterator is None:
                    raise StopIteration("No more rows to iterate for statement: " + self._statement.name)
                value = next(self._full_load_iterator)
            else:
                self._iterator = DataSourceRegistry.get_cyclic_data_iterator(
                    data=file_data,
                    cyclic=self.statement.cyclic,
                    pagination=self._pagination,
                )
                self._mode = self._ITERATOR_MODE
                value = next(self._iterator) if self._iterator is not None else None
        else:
            value = self._generate_value(ctx)

        # evaluate data with source script
        if self._source_script:
            if self._mode in [
                VariableTask._ITERATOR_MODE,
                VariableTask._WEIGHTED_ENTITY_MODE,
                VariableTask._FULL_LOAD_MODE,
            ]:
                # Default variable prefix and suffix
                setup_ctx = ctx
                while isinstance(setup_ctx, GenIterContext):
                    setup_ctx = setup_ctx.parent
                if not isinstance(setup_ctx, SetupContext):
                    raise ValueError(
                        f"<variable> '{self._statement.name}': expected a SetupContext at the root of the "
                        f"context chain, got {type(setup_ctx).__name__}"
                    )
                variable_prefix = self.statement.variable_prefix or setup_ctx.default_variable_prefix
                variable_suffix = self.statement.variable_suffix or setup_ctx.default_variable_suffix
                # Evaluate source script
                value = TaskUtil.evaluate_file_script_template(ctx, value, variable_prefix, variable_suffix)
            else:
                raise ValueError("sourceScripted only support datasource CSV or JSON")

        value = self._convert_generated_value(value)

        # Add variable to context for later retrieving
        if isinstance(ctx, SetupContext):
            ctx.global_variables[self._statement.name] = value
        elif isinstance(ctx, GenIterContext):
            ctx.current_variables[self._statement.name] = value
