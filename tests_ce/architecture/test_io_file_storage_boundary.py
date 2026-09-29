"""Keep file storage on the file-specific public IO facade."""

from __future__ import annotations

from datamimic_ce.engine.io import api as io_api
from datamimic_ce.engine.io.files import api as files_api


def test_file_content_storage_is_exported_only_by_files_api() -> None:
    assert "FileContentStorage" not in io_api.__all__
    assert not hasattr(io_api, "FileContentStorage")

    assert "FileContentStorage" in files_api.__all__
    assert files_api.FileContentStorage.__name__ == "FileContentStorage"
