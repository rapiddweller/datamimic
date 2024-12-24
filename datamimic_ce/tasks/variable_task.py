# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from collections.abc import Iterator
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
from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.data_sources.data_source_util import DataSourceUtil
from datamimic_ce.data_sources.weighted_entity_data_source import WeightedEntityDataSource
from datamimic_ce.entities.address_entity import AddressEntity
from datamimic_ce.entities.bank_account_entity import BankAccountEntity
from datamimic_ce.entities.bank_entity import BankEntity
from datamimic_ce.entities.city_entity import CityEntity
from datamimic_ce.entities.company_entity import CompanyEntity
from datamimic_ce.entities.country_entity import CountryEntity
from datamimic_ce.entities.credit_card_entity import CreditCardEntity
from datamimic_ce.entities.person_entity import PersonEntity
from datamimic_ce.statements.variable_statement import VariableStatement
from datamimic_ce.tasks.key_variable_task import KeyVariableTask
from datamimic_ce.tasks.task_util import TaskUtil
from datamimic_ce.utils.file_util import FileUtil
from datamimic_ce.utils.string_util import StringUtil


class VariableTask(KeyVariableTask):
    _iterator: Iterator[Any] | None
    _ITERATOR_MODE: Final = "iterator"
    _ENTITY_MODE: Final = "entity_builder"
    _WEIGHTED_ENTITY_MODE: Final = "weighted_entity"
    _ITERATION_SELECTOR_MODE: Final = "iteration_selector"
    _RANDOM_DISTRIBUTION_MODE: Final = "random_distribution"
    _LAZY_ITERATOR_MODE: Final = "lazy_iterator"

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
        seed: int
        file_data: list[dict[str, Any]] | None = None
        self._random_items_iterator = None
        is_random_distribution = self.statement.distribution in ("random", None)
        if is_random_distribution:
            # Use task_id as seed for random distribution
            seed = ctx.root.get_distribution_seed()

        # Try to init generation mode of VariableTask
        if statement.source is not None:
            source_str = statement.source
            separator = statement.separator or ctx.default_separator
            # Load data from weighted entity file
            if source_str.endswith(".wgt.ent.csv"):
                self._weighted_data_source = WeightedEntityDataSource(
                    file_path=descriptor_dir / source_str,
                    separator=separator,
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
                    if is_random_distribution:
                        self._mode = self._RANDOM_DISTRIBUTION_MODE
                        selected_data = client.get_by_page_with_query(selector)
                        self._random_items_iterator = iter(
                            DataSourceUtil.get_shuffled_data_with_cyclic(
                                selected_data, pagination, statement.cyclic, seed
                            )
                        )
                    else:
                        # global variable (setup variable, out of generate_stmt scope) don't need pagination and cyclic
                        if self._statement.is_global_variable:
                            file_data = client.get_by_page_with_query(selector)
                        # Get data source with pagination
                        else:
                            len_data = ctx.data_source_len.get(statement.full_name)
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
                if source_str.endswith("csv") or source_str.endswith("json"):
                    file_data = (
                        FileUtil.read_csv_to_dict_list(file_path=descriptor_dir / source_str, separator=separator)
                        if source_str.endswith("csv")
                        else FileUtil.read_json_to_dict_list(descriptor_dir / source_str)
                    )
                    if is_random_distribution:
                        self._random_items_iterator = iter(
                            DataSourceUtil.get_shuffled_data_with_cyclic(file_data, pagination, statement.cyclic, seed)
                        )
                        self._mode = self._RANDOM_DISTRIBUTION_MODE
                    else:
                        self._iterator = DataSourceUtil.get_cyclic_data_iterator(
                            data=file_data,
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

                        # in case of dbms product_type reflects the table name
                        product_type = statement.type or statement.name
                        # TODO: check if pagination is needed
                        file_data = client.get_by_page_with_type(product_type) if product_type is not None else None
                    # Get data from memstore
                    elif ctx.memstore_manager.contain(source_str):
                        product_type = statement.type or statement.name
                        memstore = ctx.memstore_manager.get_memstore(source_str)
                        file_data = (
                            memstore.get_all_data_by_type(product_type)
                            if is_random_distribution
                            else memstore.get_data_by_type(product_type, pagination, statement.cyclic)
                        )
                    # Get data from script in lazy mode
                    else:
                        is_lazy_source = True

                    if is_lazy_source:
                        self._iterator = None
                        self._mode = self._LAZY_ITERATOR_MODE
                    else:
                        if is_random_distribution:
                            self._random_items_iterator = (
                                iter(
                                    DataSourceUtil.get_shuffled_data_with_cyclic(
                                        file_data, pagination, statement.cyclic, seed
                                    )
                                )
                                if file_data is not None
                                else None
                            )
                            self._mode = self._RANDOM_DISTRIBUTION_MODE
                        else:
                            self._iterator = iter(file_data) if file_data is not None else None
                            self._mode = self._ITERATOR_MODE
        elif statement.entity is not None:
            # Create entity builder
            locale = statement.locale or ctx.default_locale
            dataset = statement.dataset or ctx.default_dataset
            try:
                self._entity = self._get_entity(
                    ctx,
                    entity_name=statement.entity,
                    locale=locale,
                    dataset=dataset,
                    count=1 if pagination is None else pagination.limit,
                )
            except Exception as e:
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
    def _get_entity(ctx: Context, entity_name: str, locale: str, dataset: str, count: int):
        entity_class_name, kwargs = StringUtil.parse_constructor_string(entity_name)
        if isinstance(ctx, SetupContext) and hasattr(ctx, "class_factory_util"):
            cls_factory_util = ctx.class_factory_util
        if entity_class_name == "Person":
            return PersonEntity(cls_factory_util, dataset=dataset, count=count, locale=locale, **kwargs)
        if entity_class_name == "Company":
            return CompanyEntity(
                cls_factory_util=cls_factory_util,
                locale=locale,
                dataset=dataset,
                count=count,
            )
        if entity_class_name == "City":
            return CityEntity(class_factory_util=cls_factory_util, dataset=dataset)
        if entity_class_name == "Address":
            return AddressEntity(class_factory_util=cls_factory_util, dataset=dataset)
        if entity_class_name == "CreditCard":
            return CreditCardEntity(cls_factory_util)
        if entity_class_name == "Bank":
            return BankEntity(cls_factory_util)
        if entity_class_name == "BankAccount":
            return BankAccountEntity(cls_factory_util, locale=locale, dataset=dataset)
        if entity_class_name == "Country":
            return CountryEntity(cls_factory_util)
        else:
            raise ValueError(f"Entity {entity_name} is not supported.")

    def execute(self, ctx: Context) -> None:
        """
        Generate data for element <variable>
        """
        from datamimic_ce.tasks.task_util import TaskUtil

        if self._mode == self._ITERATOR_MODE:
            value = next(self._iterator) if self._iterator is not None else None
        elif self._mode == self._ENTITY_MODE:
            self._entity.reset()
            value = self._entity
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
        elif self._mode == self._RANDOM_DISTRIBUTION_MODE:
            if self._random_items_iterator is None:
                raise StopIteration(f"No more random items to iterate for statement: {self._statement.name}")
            value = next(self._random_items_iterator)
        elif self._mode == self._LAZY_ITERATOR_MODE:
            if isinstance(self._statement, VariableStatement):
                is_random_distribution = self._statement.distribution in ("random", None)
            else:
                is_random_distribution = False
            if self._statement.source is None:
                return None
            file_data = ctx.evaluate_python_expression(self._statement.source)
            if is_random_distribution:
                self._random_items_iterator = iter(
                    DataSourceUtil.get_shuffled_data_with_cyclic(
                        file_data,
                        self._pagination,
                        self.statement.cyclic,
                        ctx.root.get_distribution_seed(),
                    )
                )
                self._mode = self._RANDOM_DISTRIBUTION_MODE
                if self._random_items_iterator is None:
                    raise StopIteration("No more random items to iterate for statement: " + self._statement.name)
                value = next(self._random_items_iterator)
            else:
                self._iterator = DataSourceUtil.get_cyclic_data_iterator(
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
                VariableTask._RANDOM_DISTRIBUTION_MODE,
            ]:
                # Default variable prefix and suffix
                setup_ctx = ctx
                while isinstance(setup_ctx, GenIterContext):
                    setup_ctx = setup_ctx.parent
                if isinstance(setup_ctx, SetupContext):
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
