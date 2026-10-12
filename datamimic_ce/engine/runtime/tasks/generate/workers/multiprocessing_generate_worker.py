# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import multiprocessing
from contextlib import suppress

from datamimic_ce.engine.dsl.api import GenerateStatement
from datamimic_ce.engine.runtime.contexts.context import WorkerContextPayload
from datamimic_ce.engine.runtime.tasks.generate.workers.generate_worker import GenerateWorker


class MultiprocessingGenerateWorker(GenerateWorker):
    """
    Worker class for generating and exporting data by page in multiprocessing using multiprocessing.
    """

    def mp_process(
        self,
        copied_context: WorkerContextPayload,
        statement: GenerateStatement,
        chunks: list[tuple[int, int]],
        page_size: int,
    ) -> dict[str, list]:
        """
        Multiprocessing process for generating, exporting data by page, and merging result.
        """
        # Execute generate task using multiprocessing
        with multiprocessing.get_context("spawn").Pool(processes=len(chunks)) as pool:
            mp_result = pool.map(
                self.mp_wrapper,
                [
                    (
                        copied_context,
                        statement,
                        worker_id,
                        chunk_start,
                        chunk_end,
                        page_size,
                    )
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
        from datamimic_ce.engine.runtime.tasks.generate.workers.generate_worker import GenerateWorker

        # Unpack arguments
        payload, stmt, worker_id, chunk_start, chunk_end, page_size = args

        context = None
        try:
            context = GenerateWorker.deserialize_worker_context(payload)

            from datamimic_ce.engine.runtime.process_titles import set_generate_worker_process_title

            set_generate_worker_process_title(
                worker_id=worker_id,
                task_id=context.root.task_id,
                statement=stmt.full_name,
                chunk=(chunk_start, chunk_end),
            )

            GenerateWorker.mp_preprocess(context, worker_id)

            result = GenerateWorker.generate_and_export_data_by_chunk(
                context, stmt, worker_id, chunk_start, chunk_end, page_size
            )
        except BaseException:
            if context is not None:
                with suppress(BaseException):
                    GenerateWorker.cleanup_worker_context(context)
            raise
        else:
            if context is not None:
                GenerateWorker.cleanup_worker_context(context)
            return result
