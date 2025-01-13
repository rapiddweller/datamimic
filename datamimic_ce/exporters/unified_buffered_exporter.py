import json
import os
import pathlib
import shutil
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.exporters.exporter import Exporter
from datamimic_ce.exporters.exporter_state_manager import ExporterStateManager
from datamimic_ce.logger import logger
from datamimic_ce.utils.multiprocessing_page_info import MultiprocessingPageInfo


class ExporterError(Exception):
    """Base class for exporter exceptions."""

    pass


class BufferFileError(ExporterError):
    """Exception raised for errors related to buffer file operations."""

    pass


class ExportError(ExporterError):
    """Exception raised during data export/upload."""

    pass


class UnifiedBufferedExporter(Exporter, ABC):
    """
    Abstract exporter that collects data until chunk size is reached.
    Manages chunking by grouping entities into files based on user-defined chunk size.
    Supports multiple formats (e.g., JSON, CSV, XML) and storage backends.
    """

    STREAM_CHUNK_SIZE = 8 * 1024 * 1024  # 8MB streaming chunks for large files
    MAX_RETRIES = 3
    RETRY_DELAY = 0.1  # seconds

    def __init__(
        self,
        exporter_type: str,
        setup_context: SetupContext,
        product_name: str,
        chunk_size: int | None,
        encoding: str | None,
    ):
        if chunk_size is not None and chunk_size <= 0:
            raise ValueError("Chunk size must be a positive integer or None for unlimited size.")

        self._exporter_type = exporter_type
        self.product_name = product_name  # Name of the product being exported
        self._encoding = encoding or setup_context.default_encoding or "utf-8"
        self._mp = setup_context.use_mp  # Multiprocessing flag
        self._task_id = setup_context.task_id  # Task ID for tracking
        self._descriptor_dir = setup_context.descriptor_dir  # Directory for storing temp files
        self._chunk_size = chunk_size  # Max entities per chunk

        # Prepare temporary buffer directory
        # self._buffer_tmp_dir = self._get_buffer_tmp_dir()
        # self._init_buffer_directory()

        # Initialize state variables
        self._is_first_write: bool | None = None
        # self._load_state()

    @property
    def encoding(self) -> str:
        return self._encoding

    @property
    def chunk_size(self) -> int | None:
        return self._chunk_size

    # def _get_buffer_tmp_dir(self) -> Path:
    #     return (
    #         self._descriptor_dir / f"temp_result_{self._task_id}{self._pid_placeholder}_exporter_"
    #         f"{self._exporter_type}_product_{self.product_name}"
    #     )
    #
    # def _init_buffer_directory(self) -> None:
    #     """Initialize buffer directory with proper synchronization and error handling."""
    #     for attempt in range(self.MAX_RETRIES):
    #         try:
    #             if self._buffer_tmp_dir.exists():
    #                 logger.debug(f"Buffer directory already exists: {self._buffer_tmp_dir}")
    #                 return
    #             else:
    #                 self._buffer_tmp_dir.mkdir(parents=True, exist_ok=True)
    #                 os.chmod(str(self._buffer_tmp_dir), 0o755)
    #                 logger.debug(f"Successfully initialized buffer directory: {self._buffer_tmp_dir}")
    #                 return
    #         except Exception as e:
    #             logger.error(f"Attempt {attempt + 1} failed to initialize buffer directory: {e}")
    #             if attempt == self.MAX_RETRIES - 1:
    #                 raise BufferFileError(
    #                     f"Failed to initialize buffer directory after {self.MAX_RETRIES} attempts: {e}"
    #                 ) from e
    #             time.sleep(self.RETRY_DELAY * (attempt + 1))
    #
    # def _get_state_meta_file(self) -> Path:
    #     return self._buffer_tmp_dir / f"state_product_{self.product_name}{self._pid_placeholder}.meta"
    #
    # def _load_state(self) -> None:
    #     """Loads the exporter state from the metadata file with retry mechanism."""
    #     state_file = self._buffer_tmp_dir / "state.meta"
    #
    #     for attempt in range(self.MAX_RETRIES):
    #         try:
    #             if state_file.exists():
    #                 with state_file.open("r", encoding=self._encoding) as f:
    #                     state = json.load(f)
    #                     self.current_counter = state.get("current_counter", 0)
    #                     self.global_counter = state.get("global_counter", 0)
    #                     self.chunk_index = state.get("chunk_index", 0)
    #                     self._is_first_write = state.get("is_first_write", True)
    #                     logger.debug(f"Loaded state from {state_file}: {state}")
    #             else:
    #                 self._init_state()
    #             return
    #         except Exception as e:
    #             logger.error(f"Attempt {attempt + 1} failed to load state: {e}")
    #             if attempt == self.MAX_RETRIES - 1:
    #                 logger.warning("Failed to load state, initializing new state")
    #                 self._init_state()
    #             time.sleep(self.RETRY_DELAY * (attempt + 1))
    #
    #     logger.error(f"Failed to load state after {self.MAX_RETRIES} attempts")
    #     raise BufferFileError(f"Failed to load state after {self.MAX_RETRIES} attempts")
    #
    # def _init_state(self) -> None:
    #     """Initialize new state variables."""
    #     self.current_counter = 0
    #     self.global_counter = 0
    #     self.chunk_index = 0
    #     self._is_first_write = True
    #     logger.debug("Initialized new state variables")
    #
    # def _save_state(self) -> None:
    #     """Saves the exporter state to the state file with retry mechanism."""
    #     state_file = self._buffer_tmp_dir / "state.meta"
    #     state = {
    #         "current_counter": self.current_counter,
    #         "global_counter": self.global_counter,
    #         "chunk_index": self.chunk_index,
    #         "is_first_write": self._is_first_write,
    #     }
    #     for attempt in range(self.MAX_RETRIES):
    #         try:
    #             with state_file.open("w", encoding=self._encoding) as f:
    #                 json.dump(state, f)
    #             logger.debug(f"Saved state to {state_file}: {state}")
    #             return
    #         except Exception as e:
    #             logger.error(f"Attempt {attempt + 1} failed to save state: {e}")
    #             if attempt == self.MAX_RETRIES - 1:
    #                 raise BufferFileError(f"Failed to save state after {self.MAX_RETRIES} attempts: {e}") from e
    #             time.sleep(self.RETRY_DELAY * (attempt + 1))
    #
    # def _load_metadata(self, metadata_file: Path) -> dict:
    #     """Loads metadata from the specified metadata file."""
    #     with metadata_file.open("r", encoding=self._encoding) as f:
    #         metadata = json.load(f)
    #     return metadata

    def _get_buffer_tmp_dir(self, worker_id: int) -> Path:
        buffer_temp_dir = (
                self._descriptor_dir / f"temp_result_{self._task_id}_pid_{worker_id}_exporter_"
                                       f"{self._exporter_type}_product_{self.product_name}"
        )
        pathlib.Path(buffer_temp_dir).mkdir(parents=True, exist_ok=True)
        return buffer_temp_dir

    def _get_buffer_file(self, worker_id: int, chunk_index: int) -> Path:
        """Get the buffer file for the current chunk."""
        buffer_file = self._get_buffer_tmp_dir(worker_id) / Path(
            f"product_{self.product_name}_pid_{worker_id}_chunk_{chunk_index}.{self.get_file_extension()}"
        )

        return buffer_file

    # def _rotate_chunk(self) -> None:
    #     """Finalizes current chunk and creates new one with proper error handling."""
    #     logger.debug(f"Rotating chunk for PID {self._worker_id} with current index {self.chunk_index}")
    #     try:
    #         self.chunk_index += 1
    #         self.current_counter = 0
    #         self._save_state()
    #         self._buffer_file = self._get_buffer_file()
    #         self._is_first_write = True
    #     except Exception as e:
    #         logger.error(f"Failed to rotate chunk: {e}")
    #         raise BufferFileError(f"Failed to rotate chunk: {e}") from e

    def _write_batch_with_retry(self, batch: list[dict], worker_id: int, chunk_idx: int) -> None:
        """Write a batch of data with retry mechanism."""
        for attempt in range(self.MAX_RETRIES):
            try:
                self._write_data_to_buffer(batch, worker_id, chunk_idx)
                return
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed to write batch: {e}")
                if attempt == self.MAX_RETRIES - 1:
                    raise BufferFileError(f"Failed to write batch after {self.MAX_RETRIES} attempts: {e}") from e
                time.sleep(self.RETRY_DELAY * (attempt + 1))

    # def _update_metadata_file(self) -> None:
    #     """Updates the metadata file with retry mechanism."""
    #     buffer_file: Path | None = self._get_buffer_file()
    #     if buffer_file:
    #         metadata_file = buffer_file.with_suffix(".meta")
    #
    #         for attempt in range(self.MAX_RETRIES):
    #             try:
    #                 with metadata_file.open("r+", encoding=self._encoding) as f:
    #                     metadata = json.load(f)
    #                     metadata["total_count"] = self.global_counter
    #                     metadata["chunk_index"] = self.chunk_index
    #                     f.seek(0)  # Move to the start of the file to overwrite
    #                     json.dump(metadata, f)
    #                     f.truncate()  # Remove any leftover data from previous writes
    #                 logger.debug(f"Updated metadata file {metadata_file} with total_count: {self.global_counter}")
    #                 return
    #             except Exception as e:
    #                 logger.error(f"Attempt {attempt + 1} failed to update metadata: {e}")
    #                 if attempt == self.MAX_RETRIES - 1:
    #                     raise BufferFileError(
    #                         f"Failed to update metadata after {self.MAX_RETRIES} attempts: {e}"
    #                     ) from e
    #                 time.sleep(self.RETRY_DELAY * (attempt + 1))

    @abstractmethod
    def _write_data_to_buffer(self, data: list[dict], worker_id: int, chunk_idx: int) -> None:
        """Writes data to the current buffer file."""
        pass

    @staticmethod
    def _validate_product(product: tuple) -> tuple[list[dict], dict | None]:
        """
        Validates the structure of a product tuple.

        :param product: Tuple in the form of (name, data) or (name, data, extra).
        :return: Tuple unpacked as (data, extra).
        :raises ValueError: If product structure is invalid.
        """
        # Check the type and length of product
        if not isinstance(product, tuple):
            raise ValueError("Product must be a tuple of (name, data) or (name, data, extra)")

        if len(product) not in {2, 3}:
            raise ValueError("Product must be a tuple of (name, data) or (name, data, extra)")

        name, data = product[:2]  # Always present
        extra = product[2] if len(product) == 3 else None

        # Check for None name or data
        if name is None or data is None:
            raise ValueError("Product must contain non-None name and data")

        # Check that extra, if present, is a dictionary
        if extra is not None and not isinstance(extra, dict):
            raise ValueError("Extra data, if present, must be a dictionary")

        return data, extra

    def consume(self, product: tuple, stmt_full_name: str, exporter_state_manager: ExporterStateManager):
        """
        Store data into buffer files.
        """

        # Validate product structure
        data, extra = self._validate_product(product)
        # logger.debug(f"Storing data for '{self.product_name}' with {len(data)} records")

        exporter_state_key = f"product_{stmt_full_name}_{self.get_file_extension()}"
        state_storage = exporter_state_manager.get_storage(exporter_state_key)

        # chunk_size = state_storage.chunk_size
        # global_counter, current_counter, chunk_index, chunk_size = exporter_state_manager.load_exporter_state(exporter_state_key)

        # Determine writing batch size
        batch_size = min(1000, self._chunk_size or len(data))

        idx = 0
        total_data = len(data)
        # logger.debug(f"Storing {total_data} records for PID {worker_id}, initial count {current_counter}")

        global_counter = state_storage.global_counter
        current_counter = state_storage.current_counter

        # Write data in batches
        while idx < total_data:
            global_counter = state_storage.global_counter
            current_counter = state_storage.current_counter

            space_left = self._chunk_size - current_counter if self._chunk_size else total_data - idx
            current_batch_size = min(batch_size, space_left)
            batch = data[idx: idx + current_batch_size]

            self._write_batch_with_retry(batch, exporter_state_manager.worker_id, state_storage.chunk_index)

            current_counter += len(batch)
            global_counter += len(batch)

            idx += len(batch)
            if self._chunk_size and current_counter >= self._chunk_size and idx < total_data:
                # Finalize chunk and rotate
                # self._finalize_buffer_file(self._get_buffer_file(exporter_state_manager.worker_id, state_storage.chunk_index))
                # Rotate chunk only if there is more data to process
                exporter_state_manager.rotate_chunk(exporter_state_key)

        # Update metadata and save state
        exporter_state_manager.save_state(exporter_state_key, global_counter, current_counter)

    # def _craft_uri(self, metadata, suffix):
    #     # Extract metadata information
    #     chunk_index = metadata.get("chunk_index", 0)
    #     total_count = metadata.get("total_count", 0)
    #     product_name = metadata.get("product_name", None)
    #     chunk_size = metadata.get("chunk_size", None)
    #
    #     # Adjust range for chunk_start and chunk_end depending on whether chunk_size is defined
    #     chunk_start = (chunk_index * self.chunk_size + 1) if self.chunk_size else 1
    #     chunk_end = min(
    #         (chunk_start + self.chunk_size - 1) if self.chunk_size else total_count,
    #         total_count,
    #     )
    #
    #     # Determine URI based on chunk size and multiprocessing
    #     if chunk_size is None:
    #         uri = f"{product_name}{self._pid_placeholder}.{suffix}"
    #     elif chunk_size == 1:
    #         uri = f"{product_name}_{chunk_start}{self._pid_placeholder}.{suffix}"
    #     else:
    #         uri = f"{product_name}_{chunk_start}_{chunk_end}{self._pid_placeholder}.{suffix}"
    #
    #     return total_count, f"{self._task_id}/{uri}"

    @abstractmethod
    def get_file_extension(self) -> str:
        """Return file extension for data content."""
        pass

    @abstractmethod
    def _get_content_type(self) -> str:
        """Return MIME type for data content."""
        pass

    def finalize_chunks(self, worker_id: int) -> None:
        """Finalize remaining chunks with error handling."""
        try:
            pattern = f"*.{self.get_file_extension()}"
            for buffer_file in self._get_buffer_tmp_dir(worker_id).glob(pattern):
                self._finalize_buffer_file(buffer_file)
        except Exception as e:
            logger.error(f"Failed to finalize chunks: {e}")
            raise ExportError(f"Failed to finalize chunks: {e}") from e

    def cleanup(self) -> None:
        """Clean up temporary files with error handling."""
        logger.info(f"Cleaning up temporary files in {self._buffer_tmp_dir}")
        if not self._buffer_tmp_dir.exists():
            return

        try:
            for file in self._buffer_tmp_dir.iterdir():
                try:
                    if file.is_file():
                        file.unlink()
                except Exception as e:
                    logger.error(f"Failed to remove file {file}: {e}")
            try:
                self._buffer_tmp_dir.rmdir()
            except Exception as e:
                logger.error(f"Failed to remove directory {self._buffer_tmp_dir}: {e}")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def save_exported_result(self) -> None:
        """Copy all temporary files to the final destination.
        If destination already exists, creates a versioned directory."""
        logger.info(f"Saving exported result for product {self.product_name}")

        base_dir_path = self._descriptor_dir / "output"
        base_name = f"{self._task_id}_{self._exporter_type}_{self.product_name}"
        exporter_dir_path = base_dir_path / base_name

        # Handle existing directory by adding version number

        exporter_dir_path.mkdir(parents=True, exist_ok=True)

        # Only move files with the correct extension
        all_buffer_tmp_dirs = self._descriptor_dir.glob(f"temp_result_{self._task_id}_pid_*_exporter_{self._exporter_type}_product_{self.product_name}")
        for buffer_tmp_dir in all_buffer_tmp_dirs:
            for file in buffer_tmp_dir.glob(f"*.{self.get_file_extension()}"):
                target_path = exporter_dir_path / file.name
                version = 1
                # If file exists, create versioned file
                while target_path.exists():
                    logger.warning(f"File {target_path} already exists. Creating version {version}")
                    base_name = file.stem  # Gets filename without extension
                    target_path = exporter_dir_path / f"{base_name}_v{version}{file.suffix}"
                    version += 1

                shutil.move(file, target_path)

    # def _reset_state(self) -> None:
    #     """Reset exporter state."""
    #     self._init_state()

    @abstractmethod
    def _finalize_buffer_file(self, buffer_file: Path) -> None:
        """Finalizes the current buffer file."""
        pass
