import shutil
from pathlib import Path

import pytest


@pytest.fixture
def xlsx_test_dir(tmp_path: Path) -> Path:
    for descriptor in Path(__file__).parent.glob("*.xml"):
        shutil.copyfile(descriptor, tmp_path / descriptor.name)
    return tmp_path
