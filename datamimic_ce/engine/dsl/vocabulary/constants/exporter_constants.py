# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

EXPORTER_CONSOLE_EXPORTER = "ConsoleExporter"
EXPORTER_LOG_EXPORTER = "LogExporter"
EXPORTER_TEST_RESULT_EXPORTER = "TestResultExporter"
EXPORTER_JSON = "JSON"
EXPORTER_CSV = "CSV"
EXPORTER_XML = "XML"
EXPORTER_TXT = "TXT"
EXPORTER_XLSX = "XLSX"
EXPORTER_DBUNIT = "DbUnit"
EXPORTER_FIXED_WIDTH = "FixedWidth"

# Bare target names that resolve to a built-in exporter before any client or memstore id (#730).
BUILTIN_TARGET_NAMES = frozenset(
    {
        EXPORTER_CONSOLE_EXPORTER,
        EXPORTER_LOG_EXPORTER,
        EXPORTER_TEST_RESULT_EXPORTER,
        EXPORTER_JSON,
        EXPORTER_CSV,
        EXPORTER_XML,
        EXPORTER_TXT,
        EXPORTER_XLSX,
        EXPORTER_DBUNIT,
        EXPORTER_FIXED_WIDTH,
    }
)

# File exporters write below `<descriptor_dir>/EXPORTER_OUTPUT_DIR/`; Authoring coverage ignores the same folder.
EXPORTER_OUTPUT_DIR = "output"
