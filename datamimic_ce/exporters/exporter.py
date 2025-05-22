# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datamimic_ce.exporters.exporter_state_manager import ExporterStateManager


class Exporter(ABC):
    @abstractmethod
    def open(self) -> None:
        """
        Open or initialize the exporter.
        This method can be used for setting up connections or resources.
        """
        pass

    @abstractmethod
    def consume(self, product: tuple, stmt_full_name: str, exporter_state_manager: 'ExporterStateManager') -> None:
        """
        Consume data product.

        Args:
            product: A tuple typically containing product name and data.
                     The exact structure might vary, e.g., (name, list_of_data_dicts).
            stmt_full_name: The full name of the statement that generated this product.
            exporter_state_manager: Manages state for exporters, especially for chunking.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Close or finalize the exporter.
        This method can be used for cleaning up resources,
        flushing buffers, or finalizing output.
        """
        pass
