# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import ray

from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.workers.generate_worker import GenerateWorker


class RayGenerateWorker(GenerateWorker):
    """
    Worker class for generating and exporting data by page in multiprocessing using Ray.
    """

    def mp_process(
        self,
        copied_context: SetupContext | GenIterContext,
        statement: GenerateStatement,
        chunks: list[tuple[int, int]],
        page_size: int,
        source_operation: dict | None,
    ) -> dict[str, list]:
        """
        Ray multiprocessing process for generating, exporting data by page, and merging result.
        """
        # Execute generate task using Ray
        futures = [
            self.ray_process.options(enable_task_events=False).remote(
                copied_context, statement, worker_id, chunk_start, chunk_end, page_size, source_operation
            )
            for worker_id, (chunk_start, chunk_end) in enumerate(chunks, 1)
        ]
        # Gather result from Ray workers
        ray_result = ray.get(futures)

        # Merge result from all workers by product name
        merged_result: dict[str, list] = {}
        for result in ray_result:
            for product_name, product_data_list in result.items():
                merged_result[product_name] = merged_result.get(product_name, []) + product_data_list

        return merged_result

    @staticmethod
    @ray.remote
    def ray_process(
        context: SetupContext | GenIterContext,
        stmt: GenerateStatement,
        worker_id: int,
        chunk_start: int,
        chunk_end: int,
        page_size: int,
        source_operation: dict | None,
    ) -> dict:
        """
        Ray remote function to generate and export data by page in multiprocessing.
        """
        # Preprocess serializable objects
        GenerateWorker.mp_preprocess(context, worker_id)

        return GenerateWorker.generate_and_export_data_by_chunk(
            context, stmt, worker_id, chunk_start, chunk_end, page_size, source_operation
        )
