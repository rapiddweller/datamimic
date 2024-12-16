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

from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.exporters.unified_buffered_exporter import UnifiedBufferedExporter
from datamimic_ce.logger import logger
from datamimic_ce.utils.multiprocessing_page_info import MultiprocessingPageInfo


class TXTExporter(UnifiedBufferedExporter):
    """
    Exports generated data to TXT format, saved on object storage.
    Supports chunking and can handle custom separators.
    """

    def __init__(
        self,
        setup_context: SetupContext,
        product_name: str,
        page_info: MultiprocessingPageInfo,
        chunk_size: int | None,
        separator: str | None,
        line_terminator: str | None,
        encoding: str | None,
    ):
        """
        Initializes the TXTExporter.

        Parameters:
            setup_context (SetupContext): The setup context containing configurations.
            chunk_size (int, optional): Number of records per chunk. Defaults to None.
            separator (str, optional): Separator to use between fields. Defaults to ':'.
            line_terminator (str, optional): Line terminator to use. Defaults to system's default.
            encoding (str, optional): Encoding to use. Defaults to 'utf-8'.
        """
        # Initialize instance variables
        self.separator = separator or setup_context.default_separator or ":"
        self.line_terminator = line_terminator or setup_context.default_line_separator or os.linesep or "\n"

        # Pass encoding via kwargs to the base class

        super().__init__(
            "txt", setup_context, product_name, chunk_size=chunk_size, page_info=page_info, encoding=encoding
        )
        logger.info(
            f"TXTExporter initialized with chunk size {chunk_size}, separator '{self.separator}', "
            f"encoding '{self.encoding}', line terminator '{self.line_terminator}'"
        )

    def get_file_extension(self) -> str:
        """Defines the file suffix based on the format."""
        return "txt"

    def _get_content_type(self) -> str:
        """Returns the MIME type for the data content."""
        return "text/plain"

    def _write_data_to_buffer(self, data: list[dict]) -> None:
        """Writes data to the current buffer file in TXT format."""
        try:
            buffer_file = self._get_buffer_file()
            with buffer_file.open("a", encoding=self.encoding) as txtfile:
                for record in data:
                    # Format each record as "name: item"
                    # Assuming 'record' is a dict; convert it to a string representation
                    data_string = f"{self.product_name}: {record}{self.line_terminator}"
                    txtfile.write(data_string)
            logger.debug(f"Wrote {len(data)} records to buffer file: {buffer_file}")
        except Exception as e:
            logger.error(f"Error writing data to buffer: {e}")
            raise

    def _finalize_buffer_file(self, buffer_file: Path) -> None:
        """Finalizes the current buffer file."""
        # For TXT files, no specific finalization is needed
        pass
