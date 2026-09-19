# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from dataclasses import dataclass

from datamimic_ce.contexts.setup_context import SetupContext


@dataclass(frozen=True)
class ExporterConfig:
    """The parameters every buffered file exporter shares.

    Bundling them means a cross-cutting exporter setting (chunk_size, encoding, exportUri, ...) is
    added in ONE place instead of every exporter constructor + every factory call. Format-specific
    options (CSV delimiter, XLSX sheet_name, ...) stay on the individual exporters.
    """

    setup_context: SetupContext
    product_name: str
    chunk_size: int | None
    encoding: str | None
    export_uri: str | None = None
