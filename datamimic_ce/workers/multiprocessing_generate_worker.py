# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import multiprocessing

from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.workers.generate_worker import GenerateWorker


class MultiprocessingGenerateWorker(GenerateWorker):
    """
    Worker class for generating and exporting data by page in multiprocessing using multiprocessing.
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
        Multiprocessing process for generating, exporting data by page, and merging result.
        """
        # Execute generate task using multiprocessing
        with multiprocessing.Pool(processes=len(chunks)) as pool:
            mp_result = pool.map(
                self.mp_wrapper,
                [
                    (copied_context, statement, worker_id, chunk_start, chunk_end, page_size, source_operation)
                    for worker_id, (chunk_start, chunk_end) in enumerate(chunks, 1)
                ],
            )

        # Merge result from all workers by product name
        merged_result: dict[str, list] = {}
        for result in mp_result:
            for product_name, product_data_list in result.items():
                merged_result[product_name] = merged_result.get(product_name, []) + product_data_list

        return merged_result

    @staticmethod
    def mp_wrapper(args):
        """
        Wrapper function for multiprocessing.
        """
        from datamimic_ce.workers.generate_worker import GenerateWorker

        # Unpack arguments
        context, stmt, worker_id, chunk_start, chunk_end, page_size, source_operation = args

        # Preprocess serializable objects
        GenerateWorker.mp_preprocess(context, worker_id)

        return GenerateWorker.generate_and_export_data_by_chunk(
            context, stmt, worker_id, chunk_start, chunk_end, page_size, source_operation
        )
