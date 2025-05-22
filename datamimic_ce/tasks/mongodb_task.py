# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.clients.mongodb_client import MongoDBClient
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.statements.mongodb_statement import MongoDBStatement
from datamimic_ce.tasks.task import SetupSubTask


class MongoDBTask(SetupSubTask):
    def __init__(self, statement: MongoDBStatement):
        self._statement = statement

    @property
    def statement(self) -> MongoDBStatement:
        return self._statement

from datamimic_ce.logger import logger # Import logger

    def execute(self, ctx: SetupContext):
        client = MongoDBClient(self._statement.mongodb_connection_config)
        ctx.add_client(self._statement.mongodb_id, client)

        # If the MongoDB statement defines an operation, execute a count query for validation/logging.
        op_type = self._statement.operation
        collection = self._statement.collection

        if op_type and collection:
            logger.info(
                f"MongoDB Task for ID '{self._statement.mongodb_id}': Found operation '{op_type}' "
                f"for collection '{collection}'. Performing a count for validation."
            )
            try:
                count = -1
                if op_type == "find":
                    # Ensure filter_dict is not None, default to {} if not provided by statement
                    filter_d = self._statement.filter if self._statement.filter is not None else {}
                    count = client.count_find_query_length(collection_name=collection, filter_dict=filter_d)
                    logger.info(
                        f"MongoDB Task ID '{self._statement.mongodb_id}': 'find' operation count on collection "
                        f"'{collection}' (with provided filter) resulted in {count} documents."
                    )
                elif op_type == "aggregate":
                    # Ensure pipeline_list is not None, default to empty list if not provided
                    pipeline_l = self._statement.pipeline if self._statement.pipeline is not None else []
                    if not pipeline_l: # count_aggregate_query_length needs a pipeline, even if it's just for a full count
                         logger.warning(
                            f"MongoDB Task ID '{self._statement.mongodb_id}': 'aggregate' operation for collection "
                            f"'{collection}' has an empty pipeline. Count may reflect all documents if pipeline was expected."
                        )
                    count = client.count_aggregate_query_length(collection_name=collection, pipeline_list=pipeline_l)
                    logger.info(
                        f"MongoDB Task ID '{self._statement.mongodb_id}': 'aggregate' operation count on collection "
                        f"'{collection}' (with provided pipeline) resulted in {count} potential documents."
                    )
                else:
                    logger.info(
                        f"MongoDB Task ID '{self._statement.mongodb_id}': Operation type '{op_type}' "
                        "is not a 'find' or 'aggregate' query, no count validation performed by MongoDBTask."
                    )
            except Exception as e:
                logger.error(
                    f"MongoDB Task ID '{self._statement.mongodb_id}': Error during count validation for operation '{op_type}' "
                    f"on collection '{collection}': {e}"
                )
                # Depending on policy, might re-raise or just log. For a setup task, logging might be sufficient.
        elif self._statement.mongodb_id:
             logger.info(f"MongoDB Task for ID '{self._statement.mongodb_id}': Client registered. No specific query operation defined on the statement for validation.")
        else:
            logger.error("MongoDB Task executed for a statement with no ID.")

