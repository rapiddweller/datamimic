# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import json
from dataclasses import replace
from pathlib import Path
from typing import Any
from xml.sax.saxutils import quoteattr

from datamimic_ce.exporters.exporter_config import ExporterConfig
from datamimic_ce.exporters.unified_buffered_exporter import UnifiedBufferedExporter
from datamimic_ce.logger import logger


class DbUnitExporter(UnifiedBufferedExporter):
    """Export generated data as a dbunit flat-XML dataset (``target="DbUnit"``).

    Each record becomes a ``<table col="val"/>`` row; the table (element name) is the product name
    (``targetEntity`` -> type -> name). A ``None`` value is written as an ABSENT attribute (dbunit's
    NULL convention), a present empty string as ``col=""``. Attribute values are XML-escaped. The
    chunk buffer accumulates records as JSON lines; the ``<dataset>`` is written once at finalize.
    """

    def __init__(self, config: ExporterConfig, params: dict):
        # the row element name = the physical table/entity being written
        self._table = config.product_name
        # A dbunit dataset is a whole document; chunking would split one table across several partial
        # <dataset> files. Force a single file (ignore chunk_size).
        super().__init__("dbunit", replace(config, chunk_size=None))
        logger.info(f"DbUnitExporter initialized for table '{self._table}'")

    def get_file_extension(self) -> str:
        return "dbunit.xml"

    def _get_content_type(self) -> str:
        return "application/xml"

    def _write_data_to_buffer(self, data: list[dict[str, Any]], worker_id: int, chunk_idx: int) -> None:
        """Append each record as a JSON line (turned into a <dataset> at finalize)."""
        buffer_file = self._get_buffer_file(worker_id, chunk_idx)
        if buffer_file is None:
            return
        with buffer_file.open("a", encoding=self.encoding) as f:
            for record in data:
                f.write(json.dumps(record, default=str) + "\n")

    def _finalize_buffer_file(self, buffer_file: Path) -> None:
        """Read the JSON-line buffer and (over)write it as a dbunit flat-XML <dataset>."""
        with buffer_file.open(encoding=self.encoding) as f:
            records = [json.loads(line) for line in f if line.strip()]
        lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<dataset>"]
        for record in records:
            attrs = "".join(
                f" {col}={quoteattr(str(value))}" for col, value in record.items() if value is not None
            )
            lines.append(f"    <{self._table}{attrs}/>")
        lines.append("</dataset>")
        buffer_file.write_text("\n".join(lines) + "\n", encoding=self.encoding or "utf-8")
