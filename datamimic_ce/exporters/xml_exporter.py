# xml_exporter.py

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import xmltodict

from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.exporters.unified_buffered_exporter import UnifiedBufferedExporter
from datamimic_ce.logger import logger
from datamimic_ce.utils.multiprocessing_page_info import MultiprocessingPageInfo


class ExporterError(Exception):
    """Custom exception class for exporter errors."""

    pass


class XMLExporter(UnifiedBufferedExporter):
    """
    Export generated data to XML saved on object storage.
    Supports chunking and handles data conversion to XML format.
    """

    def __init__(
        self,
        setup_context: SetupContext,
        product_name: str,
        page_info: MultiprocessingPageInfo,
        chunk_size: Optional[int],
        root_element: Optional[str],
        item_element: Optional[str],
    ):
        """
        Initializes the XMLExporter.

        Parameters:
            setup_context (SetupContext): The setup context containing configurations.
            chunk_size (int, optional): Number of records per chunk. Defaults to None.
            root_element (str, optional): The root element name for the XML. Defaults to 'list'.
            item_element (str, optional): The element name for each item. Defaults to 'item'.
        """
        # Initialize instance variables
        self.root_element = root_element or "list"
        self.item_element = item_element or "item"

        super().__init__(
            exporter_type="xml",
            setup_context=setup_context,
            product_name=product_name,
            chunk_size=chunk_size,
            page_info=page_info,
        )
        logger.info(
            f"XMLExporter initialized with chunk size {chunk_size}, root element '{self.root_element}', "
            f"item element '{self.item_element}', encoding '{self.encoding}'"
        )

    def get_file_extension(self) -> str:
        """Defines the file suffix based on the format."""
        return "xml"

    def _get_content_type(self) -> str:
        """Returns the MIME type for the data content."""
        return "application/xml"

    def _write_data_to_buffer(self, data: list[dict[str, Any]]) -> None:
        """
        Writes data to the current buffer file in XML format.

        Parameters:
            data (List[Dict[str, Any]]): List of data records to write.
        """
        try:
            # Convert list of dicts to XML string
            items_xml = ""
            for record in data:
                # Ensure all values are strings and handle attributes
                sanitized_record = self._sanitize_record(record)
                item_xml = xmltodict.unparse(
                    {self.item_element: sanitized_record},
                    attr_prefix="@",
                    cdata_key="#text",
                    full_document=False,
                )
                items_xml += item_xml + "\n"  # Add newline for readability

            buffer_file = self._get_buffer_file()
            # If buffer does not exist or is empty, start with the root element
            if not buffer_file.exists() or buffer_file.stat().st_size == 0:
                with buffer_file.open("w", encoding=self.encoding) as xmlfile:
                    xmlfile.write(f"<{self.root_element}>\n")
                logger.debug(f"Created root element in buffer file: {buffer_file}")

            # Append items to the root element
            with buffer_file.open("a", encoding=self.encoding) as xmlfile:
                xmlfile.write(items_xml)
            logger.debug(f"Wrote {len(data)} records to buffer file: {buffer_file}")

        except Exception as e:
            logger.error(f"Error writing data to buffer: {e}")
            raise ExporterError(f"Error writing data to buffer: {e}") from e

    @staticmethod
    def _sanitize_record(data: dict[str, Any]) -> dict[str, str | dict[str, Any]] | list[dict[str, Any]] | str:
        """
        Recursively sanitize the record by converting values to strings,
        handling attributes, and formatting datetime objects.

        Parameters:
            data (dict): The data record to sanitize.

        Returns:
            dict: Sanitized data with string values and attribute prefixes.
        """
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if value is None:
                    # Set None values as empty strings
                    sanitized[key] = ""
                else:
                    sanitized[key] = XMLExporter._sanitize_record(value)
            return sanitized
        elif isinstance(data, list):
            return [XMLExporter._sanitize_record(item) for item in data]
        elif isinstance(data, datetime):
            return data.strftime("%Y-%m-%d")
        elif isinstance(data, float):
            return str(data)
        elif isinstance(data, bool):
            return str(data).lower()
        else:
            return str(data)

    def _finalize_buffer_file(self, buffer_file: Path) -> None:
        """Finalizes the current buffer file by closing the root element."""
        try:
            with buffer_file.open("r+", encoding=self.encoding) as xmlfile:
                # run to the endpoint to check last line, if last line is not close root add close root
                last_line = list(xmlfile)[-1]
                if last_line != f"</{self.root_element}>":
                    xmlfile.write(f"</{self.root_element}>")
            logger.debug(f"Finalized XML file: {buffer_file}")
        except Exception as e:
            logger.error(f"Error finalizing buffer file: {e}")
            raise ExporterError(f"Error finalizing buffer file: {e}") from e

    def _reset_state(self):
        """Resets the exporter state for reuse."""
        super()._reset_state()
        logger.debug("XMLExporter state has been reset.")
