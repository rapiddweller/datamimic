# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/


from datamimic_ce.clients.mongodb_client import MongoDBClient
from datamimic_ce.constants.convention_constants import NAME_SEPARATOR
from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.logger import logger
from datamimic_ce.model.generate_model import GenerateModel
from datamimic_ce.statements.composite_statement import CompositeStatement
from datamimic_ce.statements.statement import Statement
from datamimic_ce.statements.statement_util import StatementUtil


class GenerateStatement(CompositeStatement):
    def __init__(self, model: GenerateModel, parent_stmt: Statement):
        name = model.name
        super().__init__(name, parent_stmt)
        self._count = model.count
        self._source = model.source
        self._cyclic = model.cyclic
        self._source_script = model.source_scripted
        self._type = model.type
        self._selector = model.selector
        self._separator = model.separator
        self._targets: set[str] = StatementUtil.parse_consumer(model.target)
        self._page_size = model.page_size
        self._source_uri = model.source_uri
        self._container = model.container
        self._storage_id = model.storage_id or "default-datamimic-minio"
        self._mp = model.multiprocessing
        self._export_uri = model.export_uri
        self._distribution = model.distribution
        self._variable_prefix = model.variable_prefix
        self._variable_suffix = model.variable_suffix
        self._converter = model.converter
        self._bucket = model.bucket

    @property
    def count(self):
        return self._count

    def get_int_count(self, ctx: Context):
        """
        Get count as int value of GenerateStatement

        :param ctx:
        :return:
        """
        return StatementUtil.get_int_count(count=self._count, ctx=ctx)

    @property
    def source(self) -> str:
        return self._source

    @property
    def cyclic(self) -> bool:
        return self._cyclic

    @property
    def source_script(self) -> bool:
        return self._source_script

    @property
    def type(self) -> str:
        return self._type

    @property
    def selector(self) -> str:
        return self._selector

    @property
    def separator(self) -> str:
        return self._separator

    @property
    def targets(self) -> set[str]:
        return self._targets

    @property
    def page_size(self) -> int:
        return self._page_size

    @property
    def source_uri(self) -> str:
        return self._source_uri

    @property
    def container(self) -> str:
        return self._container

    @property
    def storage_id(self) -> str:
        return self._storage_id

    @property
    def multiprocessing(self) -> bool:
        return self._mp

    @property
    def export_uri(self) -> str:
        return self._export_uri

    @property
    def distribution(self) -> str:
        return self._distribution

    @property
    def variable_prefix(self) -> str:
        return self._variable_prefix

    @property
    def variable_suffix(self) -> str:
        return self._variable_suffix

    @property
    def converter(self) -> str:
        return self._converter

    @property
    def bucket(self) -> str:
        return self._bucket

    def contain_mongodb_upsert(self, setup_context: SetupContext) -> bool:
        """
        Check if GenerateStatement contains consumer mongodb.upsert

        :param setup_context:
        :return:
        """
        for consumer_str in self._targets:
            if "." in consumer_str:
                consumer, operation = consumer_str.split(".")
                if operation == "upsert" and isinstance(setup_context.get_client_by_id(consumer), MongoDBClient):
                    return True
        return False

    def retrieve_sub_statement_by_fullname(self, name: str) -> "GenerateStatement":
        """
        Review sub GenerateStatement by statement fullname
        :param name:
        :return:
        """
        from datamimic_ce.statements.condition_statement import ConditionStatement

        try:
            # 1. Check if name is the same as current statement
            if name == self.name:
                return self
            else:
                # 2. Continue checking sub statements
                # Remove current statement name from fullname
                segments = name.split(NAME_SEPARATOR)
                segments.pop(0)
                next_stmt_name = segments[0]
                name = NAME_SEPARATOR.join(segments)
                for sub_stmt in self.sub_statements:
                    if next_stmt_name == sub_stmt.name and isinstance(sub_stmt, GenerateStatement):
                        return sub_stmt.retrieve_sub_statement_by_fullname(name)
                    elif isinstance(sub_stmt, ConditionStatement):
                        condition_result = sub_stmt.retrieve_executed_sub_gen_statement_by_name(name)
                        if condition_result:
                            return condition_result

        except IndexError as e:
            logger.error(f"Error when retrieve sub statement by fullname '{name}': {e}")
        return None
