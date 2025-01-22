# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import os

import dill
import ray

from datamimic_ce.config import settings
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.logger import setup_logger
from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.workers.generate_worker import GenerateWorker


class RayGenerateWorker(GenerateWorker):
    """
    Worker class for generating and exporting data by page in multiprocessing using Ray.
    """

    @staticmethod
    @ray.remote
    def generate_and_export_data_by_chunk_mp(
            context: SetupContext | GenIterContext,
            stmt: GenerateStatement,
            worker_id: int,
            chunk_start: int,
            chunk_end: int,
            page_size: int,
    ) -> dict:
        """
        Ray remote function to generate and export data by page in multiprocessing.
        """
        loglevel = os.getenv("LOG_LEVEL", "INFO")
        setup_logger(logger_name=settings.DEFAULT_LOGGER, task_id=context.root.task_id, level=loglevel)

        # Deserialize multiprocessing arguments
        context.root.namespace.update(dill.loads(context.root.namespace_functions))
        context.root.generators = dill.loads(context.root.generators)

        return RayGenerateWorker.generate_and_export_data_by_chunk(context, stmt, worker_id, chunk_start, chunk_end,
                                                                   page_size)
