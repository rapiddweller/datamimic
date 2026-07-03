# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import base64
import csv
import os
from pathlib import Path

from datamimic_ce.exporters.exporter_config import ExporterConfig
from datamimic_ce.exporters.unified_buffered_exporter import UnifiedBufferedExporter
from datamimic_ce.logger import logger


class CSVExporter(UnifiedBufferedExporter):
    """
    Export generated data to CSV saved on Minio server
    """

    def __init__(self, config: ExporterConfig, params: dict):
        setup_context = config.setup_context
        self.fieldnames = params.get("fieldnames") or []
        self._task_id = setup_context.task_id
        # Retrieve delimiter/quoting from params or use setup defaults
        self.delimiter = params.get("delimiter") or setup_context.default_separator or ","
        self.quotechar = params.get("quotechar") or '"'
        self.quoting = params.get("quoting") or csv.QUOTE_MINIMAL
        self.line_terminator = (
            params.get("line_terminator") or setup_context.default_line_separator or os.linesep or "\n"
        )
        super().__init__("csv", config)
        logger.info(
            f"CSVExporter initialized with chunk size {config.chunk_size}, fieldnames '{self.fieldnames}', "
            f"encoding '{self._encoding}', delimiter '{self.delimiter}'"
        )

    def _write_data_to_buffer(self, data: list[dict], worker_id: int, chunk_idx: int) -> None:
        """Writes data to the current buffer file in CSV format."""
        try:
            buffer_file = self._get_buffer_file(worker_id, chunk_idx)
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
                    if any(isinstance(v, bytes | bytearray) for v in record.values()):
                        # binary cell -> base64 text (csv would otherwise write the b'...' repr)
                        record = {
                            k: base64.b64encode(v).decode("ascii") if isinstance(v, bytes | bytearray) else v
                            for k, v in record.items()
                        }
                    writer.writerow(record)
            logger.debug(f"Wrote {len(data)} records to buffer file: {buffer_file}")
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
