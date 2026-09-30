"""Keep file storage on the file-specific public IO facade."""

from __future__ import annotations

import pytest

from datamimic_ce.engine.io import api as io_api
from datamimic_ce.engine.io.files import api as files_api
from datamimic_ce.engine.io.files import cache as files_cache
from datamimic_ce.engine.io.files import readers as file_readers


def test_file_content_storage_is_exported_only_by_files_api() -> None:
    assert "FileContentStorage" not in io_api.__all__
    assert not hasattr(io_api, "FileContentStorage")

    assert "FileContentStorage" in files_api.__all__
    assert files_api.FileContentStorage is files_cache.FileContentStorage


def test_file_util_remains_owned_by_the_file_api() -> None:
    assert "FileUtil" not in io_api.__all__
    assert "FileUtil" in files_api.__all__
    assert files_api.FileUtil is file_readers.FileUtil


def test_io_root_does_not_allow_direct_file_util_import() -> None:
    with pytest.raises(ImportError):
        exec("from datamimic_ce.engine.io.api import FileUtil")


def test_io_root_does_not_allow_aliased_file_util_import() -> None:
    with pytest.raises(ImportError):
        exec("from datamimic_ce.engine.io.api import FileUtil as IOFileUtil")


def test_io_root_does_not_allow_local_module_file_util_access() -> None:
    with pytest.raises(AttributeError):
        exec("from datamimic_ce.engine.io import api as local_api\nlocal_api.FileUtil")


def test_io_root_does_not_allow_parent_package_file_util_access() -> None:
    with pytest.raises(AttributeError):
        exec("from datamimic_ce.engine import io as parent_io\nparent_io.api.FileUtil")
