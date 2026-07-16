# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import inspect
from collections.abc import Iterator
from random import Random
from typing import Any, Final

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
from datamimic_ce.logger import logger
from datamimic_ce.statements.variable_statement import VariableStatement
from datamimic_ce.tasks.key_variable_task import KeyVariableTask
from datamimic_ce.tasks.task import CommonSubTask
from datamimic_ce.tasks.task_util import TaskUtil
from datamimic_ce.tasks.variable_iterator import VariableIterator
from datamimic_ce.utils.domain_class_util import DomainClassUtil
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
        force_full_pool = self._storage_mode is not None

        # Try to init generation mode of VariableTask
        if statement.source is not None:
            plan = DataSourceRegistry.plan_variable_source(
                ctx,
                statement,
                pagination,
                force_full_pool=force_full_pool,
            )
            if plan.kind == "weighted":
                if plan.weighted_source is None:
                    raise RuntimeError("weighted variable source plan has no data source")
                self._weighted_data_source = plan.weighted_source
                self._mode = self._WEIGHTED_ENTITY_MODE
            elif plan.kind == "iteration_selector":
                if plan.client is None or plan.selector is None:
                    raise RuntimeError("iteration-selector plan is incomplete")
                self._client = plan.client
                self._selector = plan.selector
                self._prefix = plan.prefix
                self._suffix = plan.suffix
                self._mode = self._ITERATION_SELECTOR_MODE
            elif plan.kind == "lazy":
                self._iterator = None
                self._mode = self._LAZY_ITERATOR_MODE
            elif plan.kind == "storage":
                self._data_list = list(plan.data) if plan.data is not None else []
                if self._storage_mode == "data":
                    self._data_list = [DotableDict(row) if isinstance(row, dict) else row for row in self._data_list]
                self._storage_row_counter = 0
                self._mode = self._STORAGE_MODE
            elif plan.kind == "full_load":
                self._full_load_iterator = iter(plan.data) if plan.data is not None else None
                self._mode = self._FULL_LOAD_MODE
            else:
                self._iterator = iter(plan.data) if plan.data is not None else None
                self._mode = self._ITERATOR_MODE
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
            value = DataSourceRegistry.load_variable_iteration_selector(
                ctx, self._client, self._selector, self._prefix, self._suffix
            )
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
            source_iterator = DataSourceRegistry.load_variable_lazy_source(ctx, self._statement, self._pagination)
            if loads_all:
                self._full_load_iterator = source_iterator
                self._mode = self._FULL_LOAD_MODE
                if self._full_load_iterator is None:
                    raise StopIteration("No more rows to iterate for statement: " + self._statement.name)
                value = next(self._full_load_iterator)
            else:
                self._iterator = source_iterator
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
