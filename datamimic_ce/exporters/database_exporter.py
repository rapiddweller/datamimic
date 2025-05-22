# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any, TYPE_CHECKING

from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.exporters.exporter import Exporter

if TYPE_CHECKING:
    from datamimic_ce.exporters.exporter_state_manager import ExporterStateManager


class DatabaseExporter(Exporter):
    def __init__(self, client: RdbmsClient):
        self._client = client

    def open(self) -> None:
        """Initialize or open the database exporter."""
        # For RDBMS clients, connection is typically managed per operation or via engine pooling
        pass

    def consume(self, product: tuple, stmt_full_name: str, exporter_state_manager: 'ExporterStateManager') -> None:
        """
        Write data into SQL database.

        Args:
            product: Tuple containing (name, data_list, optional_metadata_dict).
                     Example: ('my_table', [{'col1': 1, 'col2': 'a'}, {'col1': 2, 'col2': 'b'}])
                              ('my_table', [...], {'type': 'actual_table_name_if_different'})
            stmt_full_name: The full name of the statement (unused in this exporter).
            exporter_state_manager: State manager (unused in this exporter).
        """
        if not isinstance(product, tuple) or len(product) < 2:
            # Or raise an error, depending on desired strictness
            print(f"Invalid product format for DatabaseExporter: {product}")
            return

        name, data, *rest = product
        
        if not isinstance(data, list) or not data:
            return # No data to insert

        # Check if the third element is a metadata dictionary
        table_name_to_use = name
        if len(rest) > 0 and isinstance(rest[0], dict):
            metadata = rest[0]
            table_name_to_use = metadata.get("type", name) # Use 'type' from metadata if present

        self._client.insert(table_name_to_use, data)

    def close(self) -> None:
        """Close or finalize the database exporter."""
        # RDBMS client typically manages its own connections/engine disposal if necessary,
        # or it's handled at a higher context level.
        pass
