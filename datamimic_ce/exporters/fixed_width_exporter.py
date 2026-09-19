# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path

from datamimic_ce.exporters.exporter_config import ExporterConfig
from datamimic_ce.exporters.unified_buffered_exporter import UnifiedBufferedExporter
from datamimic_ce.logger import logger
from datamimic_ce.utils.file_util import FileUtil


class FixedWidthExporter(UnifiedBufferedExporter):
    """Export generated data to a fixed-width column file (migration parity
    with legacy fixed-width demo descriptors). Writes the same '# name[width],...' spec header the reader
    (FileUtil.read_fixed_width_to_dict_list) expects, so the written file round-trips through a
    plain <generate source="....fcw"> with zero extra plumbing."""

    def __init__(self, config: ExporterConfig, params: dict):
        columns = params.get("columns")
        if not columns:
            raise ValueError(
                "FixedWidthExporter requires a 'columns' param, e.g. "
                "target=\"FixedWidth(columns='id[8r0],name[30]')\" - it cannot be self-describing "
                "on write since the file doesn't exist yet."
            )
        self.columns = columns
        self.fields = FileUtil.parse_fixed_width_spec(columns)
        super().__init__("fcw", config)
        logger.info(f"FixedWidthExporter initialized with columns '{self.columns}'")

    def _write_data_to_buffer(self, data: list[dict], worker_id: int, chunk_idx: int) -> None:
        try:
            buffer_file = self._get_buffer_file(worker_id, chunk_idx)
            if buffer_file is None:
                return
            write_header = not buffer_file.exists()
            with buffer_file.open("a", encoding=self._encoding) as f:
                if write_header:
                    f.write(f"# {self.columns}\n")
                for record in data:
                    line = "".join(
                        str(record.get(name, "")).rjust(width, pad_char)
                        if right_aligned
                        else str(record.get(name, "")).ljust(width, pad_char)
                        for name, width, right_aligned, pad_char in self.fields
                    )
                    f.write(line + "\n")
            logger.debug(f"Wrote {len(data)} records to buffer file: {buffer_file}")
        except Exception as e:
            logger.error(f"Error writing data to buffer: {e}")
            raise

    def get_file_extension(self) -> str:
        return "fcw"

    def _get_content_type(self) -> str:
        return "text/plain"

    def _finalize_buffer_file(self, buffer_file: Path) -> None:
        pass
