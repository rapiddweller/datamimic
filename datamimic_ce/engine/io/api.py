"""Runtime-facing data-source and client boundary."""

from datamimic_ce.engine.io.client_operations import (
    count_query_length,
    create_mongodb_client,
    create_rdbms_client,
    database_count_query_length,
    database_count_table_length,
    database_get_by_page_with_query,
    database_get_by_page_with_type,
    database_get_random_rows_by_columns,
    dispose_client_engine,
    is_database_client,
    is_mongodb_client,
    is_rdbms_client,
    mongodb_count_collection,
    rdbms_get_current_sequence_number,
    rdbms_increase_sequence_number,
    uses_mysql_sequence_storage,
)
from datamimic_ce.engine.io.clients.client import Client
from datamimic_ce.engine.io.connection_config.mongodb_connection_config import MongoDBConnectionConfig
from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig
from datamimic_ce.engine.io.contracts import DataSourcePagination, SmokeExportRequest
from datamimic_ce.engine.io.data_sources.data_source_registry import DataSourceRegistry
from datamimic_ce.engine.io.data_sources.weighted_data_source import WeightedDataSource
from datamimic_ce.engine.io.data_sources.weighted_entity_data_source import WeightedEntityDataSource
from datamimic_ce.engine.io.exporters.console_exporter import ConsoleExporter
from datamimic_ce.engine.io.exporters.database_exporter import DatabaseExporter
from datamimic_ce.engine.io.exporters.exporter import Exporter
from datamimic_ce.engine.io.exporters.exporter_config import ExporterConfig
from datamimic_ce.engine.io.exporters.exporter_state_manager import ExporterStateManager
from datamimic_ce.engine.io.exporters.exporter_util import ExporterUtil, buffered_exporter_names
from datamimic_ce.engine.io.exporters.log_exporter import LogExporter
from datamimic_ce.engine.io.exporters.memstore import Memstore
from datamimic_ce.engine.io.exporters.mongodb_exporter import MongoDBExporter
from datamimic_ce.engine.io.exporters.test_result_exporter import TestResultExporter
from datamimic_ce.engine.io.exporters.unified_buffered_exporter import UnifiedBufferedExporter
from datamimic_ce.engine.io.exporters.xml_exporter import XMLExporter
from datamimic_ce.engine.io.file_cache import FileContentStorage
from datamimic_ce.engine.io.files import FileUtil


def smoke_export(request: SmokeExportRequest) -> int:
    from datamimic_ce.engine.io.exporters.smoke_export import smoke_export as _smoke_export

    return _smoke_export(request)

__all__ = [
    "Client",
    "DataSourcePagination",
    "DataSourceRegistry",
    "ExporterConfig",
    "Exporter",
    "DatabaseExporter",
    "ConsoleExporter",
    "LogExporter",
    "ExporterStateManager",
    "ExporterUtil",
    "FileContentStorage",
    "FileUtil",
    "MongoDBConnectionConfig",
    "MongoDBExporter",
    "Memstore",
    "RdbmsConnectionConfig",
    "SmokeExportRequest",
    "TestResultExporter",
    "UnifiedBufferedExporter",
    "WeightedDataSource",
    "WeightedEntityDataSource",
    "XMLExporter",
    "buffered_exporter_names",
    "count_query_length",
    "create_mongodb_client",
    "create_rdbms_client",
    "database_count_table_length",
    "database_count_query_length",
    "database_get_by_page_with_query",
    "database_get_by_page_with_type",
    "database_get_random_rows_by_columns",
    "dispose_client_engine",
    "is_database_client",
    "is_mongodb_client",
    "is_rdbms_client",
    "mongodb_count_collection",
    "rdbms_get_current_sequence_number",
    "rdbms_increase_sequence_number",
    "smoke_export",
    "uses_mysql_sequence_storage",
]
