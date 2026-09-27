# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExporterConfig:
    """Scalar settings shared by buffered exporters."""

    product_name: str
    chunk_size: int | None
    encoding: str | None
    export_uri: str | None
    default_encoding: str
    default_separator: str
    default_line_separator: str
    descriptor_dir: Path
    task_id: str
    use_mp: bool | None
    track_serialized_rows: bool = False
