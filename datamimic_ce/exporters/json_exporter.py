import json
import os
from datetime import datetime
from pathlib import Path

from bson import ObjectId

from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.exporters.unified_buffered_exporter import UnifiedBufferedExporter
from datamimic_ce.logger import logger
from datamimic_ce.utils.multiprocessing_page_info import MultiprocessingPageInfo


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that converts datetime objects to ISO format."""

    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        elif isinstance(o, ObjectId):
            return str(o)
        return super().default(o)


class JsonExporter(UnifiedBufferedExporter):
    """
    Exports generated data to JSON or NDJSON format, saved on object storage.
    Supports chunking and format configuration.
    """

    def __init__(
        self,
        setup_context: SetupContext,
        product_name: str,
        page_info: MultiprocessingPageInfo,
        chunk_size: int | None,
        use_ndjson: bool | None,
        encoding: str | None,
    ):
        self.use_ndjson = use_ndjson
        self._task_id = setup_context.task_id
        super().__init__(
            "json", setup_context, product_name, chunk_size=chunk_size, page_info=page_info, encoding=encoding
        )

        logger.info(f"JsonExporter initialized with chunk size {chunk_size} and NDJSON format: {use_ndjson}")

    def _write_data_to_buffer(self, data: list[dict]) -> None:
        """Writes data to the current buffer file in NDJSON format."""
        try:
            buffer_file = self._get_buffer_file()
            # Open buffer file in append mode
            with buffer_file.open("a+") as file:
                # Handle chunk size == 1
                if self.chunk_size == 1:
                    # Write in JSON format
                    if data:
                        # Write single record directly
                        json.dump(data[0], file, cls=DateTimeEncoder, indent=4)
                        file.write("\n")
                # Write in NDJSON format
                elif self.use_ndjson:
                    # Write records one at a time
                    for record in data:
                        json.dump(record, file, cls=DateTimeEncoder)
                        file.write("\n")
                        del record  # Free memory after each record
                else:
                    file.seek(0, os.SEEK_END)
                    if file.tell() == 0:
                        file.write("[\n")
                    else:
                        file.seek(file.tell() - 1, os.SEEK_SET)
                        last_char = file.read(1)
                        if last_char != "[":
                            file.write(",\n")

                    # Write records one at a time
                    for i, record in enumerate(data):
                        json.dump(record, file, cls=DateTimeEncoder)
                        if i < len(data) - 1:
                            file.write(",\n")
                        else:
                            file.write("\n")
                        del record  # Free memory after each record
                logger.debug(f"Wrote {len(data)} records to buffer file: {buffer_file}")
            # Log the number of records written
            logger.debug(f"Wrote {len(data)} records to buffer file: {buffer_file}")
        except Exception as e:
            logger.error(f"Error occurred while writing to buffer file: {e}")
            raise e

    def _finalize_buffer_file(self, buffer_file: Path) -> None:
        """Finalizes the buffer file by ensuring it is a valid JSON array and write to output."""
        if not self.use_ndjson and (self.chunk_size is None or self.chunk_size > 1):
            with buffer_file.open("r+b") as file:
                file.seek(0, os.SEEK_END)  # Move to the end of file
                if file.tell() == 0:
                    # File is empty, nothing to do
                    return

                # Read backwards to find the last non-whitespace character
                position = file.tell() - 1
                while position >= 0:
                    file.seek(position)
                    last_char = file.read(1)
                    if last_char not in b" \n\r\t":
                        break
                    position -= 1
                else:
                    # File contains only whitespace
                    return

                if last_char == b"]":
                    # File is already finalized
                    logger.debug(f"Buffer file {buffer_file} is already finalized.")
                    return
                elif last_char == b",":
                    # Remove the last comma
                    file.seek(position)
                    file.truncate()
                    logger.debug(f"Removed trailing comma from buffer file {buffer_file}.")

                # Append the closing bracket
                file.write(b"]")
                file.flush()
                logger.debug(f"Appended closing bracket to buffer file {buffer_file}.")

    def get_file_extension(self) -> str:
        """Defines the file suffix based on the format."""
        return "ndjson" if self.use_ndjson else "json"

    def _get_content_type(self) -> str:
        """Returns the content type based on the format."""
        return "application/x-ndjson" if self.use_ndjson else "application/json"

    def _reset_state(self):
        """Resets the exporter state for reuse."""

        super()._reset_state()
        logger.debug(f"{self.__class__.__name__} state has been reset.")
