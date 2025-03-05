import pathlib
import shutil
import time
from abc import ABC, abstractmethod
from pathlib import Path

from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.exporters.exporter import Exporter
from datamimic_ce.exporters.exporter_state_manager import ExporterStateManager
from datamimic_ce.logger import logger


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

    @property
    def encoding(self) -> str:
        return self._encoding

    @property
    def chunk_size(self) -> int | None:
        return self._chunk_size

    def _get_buffer_tmp_dir(self, worker_id: int) -> Path:
        """
        Get the temporary buffer directory for the current worker.
        """
        buffer_temp_dir = (
            self._descriptor_dir / f"temp_result_{self._task_id}_pid_{worker_id}_exporter_"
            f"{self._exporter_type}_product_{self.product_name}"
        )
        # Create directory if it doesn't exist
        pathlib.Path(buffer_temp_dir).mkdir(parents=True, exist_ok=True)

        return buffer_temp_dir

    def _get_buffer_file(self, worker_id: int, chunk_index: int) -> Path:
        """
        Get the buffer file for the current chunk index.
        """
        buffer_file = self._get_buffer_tmp_dir(worker_id) / Path(
            f"product_{self.product_name}_pid_{worker_id}_chunk_{chunk_index}.{self.get_file_extension()}"
        )

        return buffer_file

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
        logger.debug(f"Storing data for '{self.product_name}' with {len(data)} records")

        # Get exporter state storage
        exporter_state_key = f"product_{stmt_full_name}_{self.get_file_extension()}"
        state_storage = exporter_state_manager.get_storage(exporter_state_key)

        # Determine writing batch size
        batch_size = min(1000, self._chunk_size or len(data))

        idx = 0
        total_data = len(data)

        # Load state from storage
        global_counter = state_storage.global_counter
        current_counter = state_storage.current_counter
        logger.debug(
            f"Storing {total_data} records for PID {exporter_state_manager.worker_id}, initial count {current_counter}"
        )

        # Write data in batches
        while idx < total_data:
            space_left = self._chunk_size - current_counter if self._chunk_size else total_data - idx
            current_batch_size = min(batch_size, space_left)
            batch = data[idx : idx + current_batch_size]

            self._write_batch_with_retry(batch, exporter_state_manager.worker_id, state_storage.chunk_index)

            current_counter += len(batch)
            global_counter += len(batch)

            idx += len(batch)
            # Finalize chunk and rotate
            if self._chunk_size and current_counter >= self._chunk_size and idx < total_data:
                # Rotate chunk only if there is more data to process
                exporter_state_manager.rotate_chunk(exporter_state_key)
                # Reload state from storage after rotation
                current_counter = state_storage.current_counter

        # Save state to storage
        exporter_state_manager.save_state(exporter_state_key, global_counter, current_counter)

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

    def save_exported_result(self) -> None:
        """
        Copy all temporary files to the final destination.
        If destination already exists, creates a versioned directory.
        """
        logger.info(f"Saving exported result for product {self.product_name}")

        base_dir_path = self._descriptor_dir / "output"
        base_name = f"{self._task_id}_{self._exporter_type}_{self.product_name}"
        exporter_dir_path = base_dir_path / base_name

        # Handle existing directory by adding version number

        exporter_dir_path.mkdir(parents=True, exist_ok=True)

        # Only move files with the correct extension
        all_buffer_tmp_dirs = self._descriptor_dir.glob(
            f"temp_result_{self._task_id}_pid_*_exporter_{self._exporter_type}_product_{self.product_name}"
        )
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

    @abstractmethod
    def _finalize_buffer_file(self, buffer_file: Path) -> None:
        """Finalizes the current buffer file."""
        pass
