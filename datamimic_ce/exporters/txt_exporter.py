#  Copyright (c) 2023 Rapiddweller Asia Co., Ltd.
#  All rights reserved.
#
#  This software and related documentation are provided under a license
#  agreement containing restrictions on use and disclosure and are
#  protected by intellectual property laws. Except as expressly permitted
#  in your license agreement or allowed by law, you may not use, copy,
#  reproduce, translate, broadcast, modify, license, transmit, distribute,
#  exhibit, perform, publish, or display any part, in any form, or by any means.
#
#  This software is the confidential and proprietary information of
#  Rapiddweller Asia Co., Ltd. ("Confidential Information"). You shall not
#  disclose such Confidential Information and shall use it only in accordance
#  with the terms of the license agreement you entered into with Rapiddweller Asia Co., Ltd.
#
import os
from pathlib import Path

from datamimic_ce.exporters.exporter_config import ExporterConfig
from datamimic_ce.exporters.unified_buffered_exporter import UnifiedBufferedExporter
from datamimic_ce.logger import logger


class TXTExporter(UnifiedBufferedExporter):
    """
    Exports generated data to TXT format, saved on object storage.
    Supports chunking and can handle custom separators.
    """

    def __init__(self, config: ExporterConfig, params: dict):
        """Initialize the TXTExporter. separator defaults to ':', line_terminator to the system default."""
        setup_context = config.setup_context
        self.separator = params.get("separator") or setup_context.default_separator or ":"
        self.line_terminator = (
            params.get("line_terminator") or setup_context.default_line_separator or os.linesep or "\n"
        )
        self._track_serialized_rows = config.track_serialized_rows
        self._serialized_records_by_buffer: dict[Path, list[str]] = {}
        super().__init__("txt", config)
        logger.info(
            f"TXTExporter initialized with chunk size {config.chunk_size}, separator '{self.separator}', "
            f"encoding '{self.encoding}', line terminator '{self.line_terminator}'"
        )

    def get_file_extension(self) -> str:
        """Defines the file suffix based on the format."""
        return "txt"

    def _get_content_type(self) -> str:
        """Returns the MIME type for the data content."""
        return "text/plain"

    def _write_data_to_buffer(self, data: list[dict], worker_id: int, chunk_idx: int) -> None:
        """Writes data to the current buffer file in TXT format."""
        try:
            buffer_file = self._get_buffer_file(worker_id, chunk_idx)
            serialized_records: list[str] = []
            with buffer_file.open("a", encoding=self.encoding, newline="") as txtfile:
                for record in data:
                    serialized = f"{self.product_name}: {record}{self.line_terminator}"
                    txtfile.write(serialized)
                    if self._track_serialized_rows:
                        serialized_records.append(serialized)
            if self._track_serialized_rows:
                self._serialized_records_by_buffer.setdefault(buffer_file, []).extend(serialized_records)
            logger.debug(f"Wrote {len(data)} records to buffer file: {buffer_file}")
        except Exception as e:
            logger.error(f"Error writing data to buffer: {e}")
            raise

    def _finalize_buffer_file(self, buffer_file: Path) -> None:
        """Finalizes the current buffer file."""
        # For TXT files, no specific finalization is needed
        pass

    def count_buffered_rows(self, worker_id: int) -> int:
        if not self._track_serialized_rows:
            raise ValueError("TXT artifact verification requires serialized-row tracking")
        count = 0
        for buffer_file in self._get_buffer_tmp_dir(worker_id).glob("*.txt"):
            with buffer_file.open("r", encoding=self.encoding, newline="") as txtfile:
                actual_content = txtfile.read()
            expected_records = self._serialized_records_by_buffer.get(buffer_file)
            if expected_records is None:
                raise ValueError(f"TXT exporter has no serialized record state for {buffer_file}")
            expected_content = "".join(expected_records)
            if actual_content != expected_content:
                raise ValueError(f"TXT export artifact differs from serialized records for {buffer_file}")
            count += len(expected_records)
        return count
