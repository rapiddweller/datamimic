# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


import base64
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.exporters.unified_buffered_exporter import UnifiedBufferedExporter
from datamimic_ce.logger import logger


class XLSXExporter(UnifiedBufferedExporter):
    """Export generated data to an .xlsx workbook (one sheet, first row = header).

    The chunk buffer accumulates records as JSON lines (append-only, matching the base exporter's
    per-batch write model); the real workbook is written once per chunk at finalize. Nested dict/list
    values are flattened to their string form, since a spreadsheet cell holds a scalar.
    """

    def __init__(
        self,
        setup_context: SetupContext,
        product_name: str,
        chunk_size: int | None,
        sheet_name: str | None,
        encoding: str | None,
    ):
        self.sheet_name = sheet_name or "data"
        super().__init__(
            exporter_type="xlsx",
            setup_context=setup_context,
            product_name=product_name,
            chunk_size=chunk_size,
            encoding=encoding,
        )
        logger.info(f"XLSXExporter initialized with chunk size {chunk_size}, sheet '{self.sheet_name}'")

    def get_file_extension(self) -> str:
        return "xlsx"

    def _get_content_type(self) -> str:
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def _write_data_to_buffer(self, data: list[dict[str, Any]], worker_id: int, chunk_idx: int) -> None:
        """Append each record as a JSON line to the chunk buffer (converted to a workbook at finalize)."""
        buffer_file = self._get_buffer_file(worker_id, chunk_idx)
        if buffer_file is None:
            return
        with buffer_file.open("a", encoding=self.encoding) as f:
            for record in data:
                f.write(json.dumps(record, default=self._json_default) + "\n")

    @staticmethod
    def _json_default(value: Any) -> str:
        if isinstance(value, datetime | date):
            return value.isoformat()
        if isinstance(value, bytes | bytearray):
            return base64.b64encode(value).decode("ascii")  # binary cell -> base64 text
        return str(value)

    @staticmethod
    def _cell(value: Any) -> Any:
        """A spreadsheet cell holds a scalar: keep numbers/bools/None/str, stringify dict/list."""
        if value is None or isinstance(value, str | int | float | bool):
            return value
        return json.dumps(value, ensure_ascii=False, default=str)

    def _finalize_buffer_file(self, buffer_file: Path) -> None:
        """Read the JSON-line buffer and (over)write it as a real .xlsx workbook."""
        from openpyxl import Workbook

        with buffer_file.open("r", encoding=self.encoding) as f:
            records = [json.loads(line) for line in f if line.strip()]

        # Header = keys in first-seen order across all records (union, order-stable).
        header: list[str] = []
        seen: set[str] = set()
        for record in records:
            for key in record:
                if key not in seen:
                    seen.add(key)
                    header.append(key)

        workbook = Workbook(write_only=True)
        sheet = workbook.create_sheet(title=self.sheet_name)
        if header:
            sheet.append(header)
            for record in records:
                sheet.append([self._cell(record.get(col)) for col in header])
        workbook.save(buffer_file)
        logger.debug(f"Wrote {len(records)} rows to XLSX file: {buffer_file}")
