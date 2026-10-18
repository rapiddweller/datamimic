"""Windows CI exercises real kernel handles and reparse-point containment."""

import os
import subprocess
from pathlib import Path

import pytest

from datamimic_ce.authoring.adapters.windows_snapshot import WindowsSnapshotRoot

pytestmark = pytest.mark.skipif(os.name != "nt", reason="requires actual Windows kernel handles")


def test_native_file_handle_matches_retained_workspace_identity(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    resource = root / "rows.csv"
    resource.write_text("id\n1\n")
    with WindowsSnapshotRoot(root) as ownership:
        ownership.validate_directory(root)
        descriptor = os.open(resource, os.O_RDONLY)
        try:
            ownership.validate_file(descriptor, resource)
        finally:
            os.close(descriptor)


def test_native_file_handle_outside_root_is_rejected_before_read(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    outside = tmp_path / "outside.csv"
    outside.write_text("private")
    with WindowsSnapshotRoot(root) as ownership:
        descriptor = os.open(outside, os.O_RDONLY)
        try:
            with pytest.raises(ValueError, match="outside"):
                ownership.validate_file(descriptor, root / "rows.csv")
        finally:
            os.close(descriptor)


def test_replaced_root_path_cannot_rebind_retained_root_identity(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    with WindowsSnapshotRoot(root) as ownership:
        root.rename(tmp_path / "original")
        root.mkdir()
        with pytest.raises(ValueError, match="identity changed"):
            ownership.validate_directory(root)


def test_native_junction_cannot_redirect_workspace_reads(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "rows.csv").write_text("private")
    junction = root / "redirect"
    subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(outside)], check=True, capture_output=True)
    try:
        with WindowsSnapshotRoot(root) as ownership:
            with pytest.raises(ValueError, match="reparse"):
                ownership.validate_directory(junction)
            descriptor = os.open(junction / "rows.csv", os.O_RDONLY)
            try:
                with pytest.raises(ValueError, match="outside"):
                    ownership.validate_file(descriptor, junction / "rows.csv")
            finally:
                os.close(descriptor)
    finally:
        os.rmdir(junction)
