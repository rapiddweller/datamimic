# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import TYPE_CHECKING
from datamimic_ce.exporters.exporter import Exporter

if TYPE_CHECKING:
    from datamimic_ce.exporters.exporter_state_manager import ExporterStateManager


class ConsoleExporter(Exporter):
    """
    Print data to console
    """

    def open(self) -> None:
        """Initialize or open the console exporter."""
        pass

    def consume(self, product: tuple, stmt_full_name: str, exporter_state_manager: 'ExporterStateManager') -> None:
        """
        Print data to console.

        Args:
            product: A tuple, typically (name, data_list).
            stmt_full_name: The full name of the statement (unused in this exporter).
            exporter_state_manager: State manager (unused in this exporter).
        """
        print()  # Add a newline for better readability between products
        if not isinstance(product, tuple) or len(product) < 2:
            print(f"Invalid product format for console output: {product}")
            return

        name = product[0]
        data = product[1]

        if not isinstance(data, list):
            print(f"{name}: {data}") # Handle cases where data might not be a list
            return

        for row_index, row in enumerate(data):
            # Check if the row itself is a tuple (e.g. from RDBMS client fetchall)
            # and try to access by attribute name if it's a SQLAlchemy Row-like object
            if hasattr(row, '_mapping'): # Support for SQLAlchemy Row objects
                 print(f"{name} (row {row_index + 1}): {dict(row._mapping)}")
            elif isinstance(row, dict):
                print(f"{name} (row {row_index + 1}): {row}")
            else:
                print(f"{name} (row {row_index + 1}): {row}")


    def close(self) -> None:
        """Close or finalize the console exporter."""
        pass
