# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import csv
import os
from pathlib import Path

from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.exporters.unified_buffered_exporter import UnifiedBufferedExporter
from datamimic_ce.logger import logger
from datamimic_ce.utils.multiprocessing_page_info import MultiprocessingPageInfo


class CSVExporter(UnifiedBufferedExporter):
    """
    Export generated data to CSV saved on Minio server
    """

    def __init__(
        self,
        setup_context: SetupContext,
        product_name: str,
        page_info: MultiprocessingPageInfo,
        chunk_size: int | None,
        fieldnames: list[str] | None,
        delimiter: str | None,
        quotechar: str | None,
        quoting: int | None,
        line_terminator: str | None,
        encoding: str | None,
    ):
        # Remove singleton pattern and initialize instance variables
        self.fieldnames = fieldnames or []
        self._task_id = setup_context.task_id

        # Retrieve encoding and delimiter from setup_context or use defaults
        self.delimiter = delimiter or setup_context.default_separator or ","
        self.quotechar = quotechar or '"'
        self.quoting = quoting or csv.QUOTE_MINIMAL
        self.line_terminator = line_terminator or setup_context.default_line_separator or os.linesep or "\n"

        super().__init__(
            exporter_type="csv",
            setup_context=setup_context,
            product_name=product_name,
            chunk_size=chunk_size,
            page_info=page_info,
            encoding=encoding,
        )
        logger.info(
            f"CSVExporter initialized with chunk size {chunk_size}, fieldnames '{fieldnames}', "
            f"encoding '{self._encoding}', delimiter '{self.delimiter}'"
        )

    def _write_data_to_buffer(self, data: list[dict]) -> None:
        """Writes data to the current buffer file in CSV format."""
        try:
            buffer_file = self._get_buffer_file()
            if buffer_file is None:
                return
            write_header = not buffer_file.exists()
            with buffer_file.open("a", newline="", encoding=self._encoding) as csvfile:
                if not self.fieldnames and data:
                    self.fieldnames = list(data[0].keys())
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=self.fieldnames,
                    delimiter=self.delimiter,
                    quotechar=self.quotechar,
                    quoting=self.quoting,
                    extrasaction="ignore",
                )
                if write_header and self.fieldnames:
                    writer.writeheader()
                for record in data:
                    writer.writerow(record)
            logger.debug(f"Wrote {len(data)} records to buffer file: {buffer_file}")
            self._is_first_write = False
        except Exception as e:
            logger.error(f"Error writing data to buffer: {e}")
            raise

    def get_file_extension(self) -> str:
        """Defines the file suffix based on the format."""
        return "csv"

    def _get_content_type(self) -> str:
        """Returns the MIME type for the data content."""
        return "text/csv"

    def _finalize_buffer_file(self, buffer_file: Path) -> None:
        # No finalization needed for CSV files
        pass

    def _reset_state(self):
        """Resets the exporter state for reuse."""
        super()._reset_state()
        logger.debug("CSVEEExporter state has been reset.")
