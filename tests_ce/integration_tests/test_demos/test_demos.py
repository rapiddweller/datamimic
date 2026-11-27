# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


import logging
import traceback
from pathlib import Path

import pytest

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class TestDemos:
    _project_root = Path(__file__).resolve().parents[3]
    _demos_dir = _project_root / "datamimic_ce" / "resources" / "demos"

    def setup_method(self):
        """Setup method run before each test."""
        if not self._demos_dir.exists():
            logger.error(f"Demos directory not found at {self._demos_dir}")
            if self._project_root.exists():
                logger.info(f"Project root exists at: {self._project_root}")
                logger.info("Contents of project root directory:")
                for item in self._project_root.iterdir():
                    logger.info(f"  - {item.name}")
            pytest.fail(f"Demos directory not found at {self._demos_dir}")

    def _run_demo_test(self, demo_path, copy_project):
        """Helper method to run a single demo test."""
        demo_name = demo_path.name
        datamimic_file = demo_path / "datamimic.xml"

        # Skip directories without a datamimic.xml file
        if not datamimic_file.exists():
            logger.warning(f"Skipping {demo_name}: No datamimic.xml file found")
            pytest.skip(f"No datamimic.xml file found in {demo_name}")

        logger.info(f"Testing demo: {demo_name}")
        logger.info(f"Using datamimic file: {datamimic_file}")

        try:
            test_engine = DataMimicTest(test_dir=copy_project(demo_path), filename="datamimic.xml")
            test_engine.test_with_timer()
            logger.info(f"Demo {demo_name} completed successfully")
        except Exception as e:
            error_msg = f"Demo {demo_name} failed with error: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            pytest.fail(error_msg)

    # Individual test methods for each demo
    def test_demo_custom_components(self, copy_project):
        """Test the custom components demo."""
        self._run_demo_test(self._demos_dir / "demo-custom-components", copy_project)

    def test_demo_database(self, copy_project):
        """Test the database demo."""
        self._run_demo_test(self._demos_dir / "demo-database", copy_project)

    def test_demo_datetime(self, copy_project):
        """Test the datetime demo."""
        self._run_demo_test(self._demos_dir / "demo-datetime", copy_project)

    def test_demo_db_mapping(self, copy_project):
        """Test the db mapping demo."""
        self._run_demo_test(self._demos_dir / "demo-db-mapping", copy_project)

    def test_demo_condition(self, copy_project):
        """Test the condition demo."""
        engine = DataMimicTest(
            test_dir=copy_project(self._demos_dir / "demo-condition"),
            filename="datamimic.xml",
            capture_test_result=True,
        )
        engine.test_with_timer()
        result = engine.capture_result()

        assert {name: len(rows) for name, rows in result.items()} == {
            "condition": 10,
            "bike": 10,
            "group_name_not_override": 10,
            "group": 10,
            "big_group": 1,
        }
        for row in result["group_name_not_override"]:
            for field in ("emptyList", "emptyList2", "emptyList3", "list2"):
                assert row[field] == []
                assert isinstance(row[field], list)
            for field in ("emptyDict", "emptyDict2", "emptyDict3", "removeElement", "removeElementorEmpty", "dict2"):
                assert row[field] == {}
                assert isinstance(row[field], dict)
            assert len(row["list"]) == 2
            assert "id" in row["dict"]

        assert all(row["same_name"] == {"age": 35} for row in result["bike"])

    def test_demo_healthcare(self, copy_project):
        """Test the healthcare demo."""
        self._run_demo_test(self._demos_dir / "demo-healthcare", copy_project)

    def test_demo_json(self, copy_project):
        """Test the JSON demo."""
        self._run_demo_test(self._demos_dir / "demo-json", copy_project)

    def test_demo_masking(self, copy_project):
        """Test the masking demo."""
        self._run_demo_test(self._demos_dir / "demo-masking", copy_project)

    def test_demo_model(self, copy_project):
        """Test the model demo."""
        self._run_demo_test(self._demos_dir / "demo-model", copy_project)

    def test_demo_postprocess(self, copy_project):
        """Test the postprocess demo."""
        self._run_demo_test(self._demos_dir / "demo-postprocess", copy_project)

    def test_demo_py_scripting(self, copy_project):
        """Test the Python scripting demo."""
        self._run_demo_test(self._demos_dir / "demo-py-scripting", copy_project)

    def test_demo_watermark(self, copy_project):
        """Test the watermark demo."""
        self._run_demo_test(self._demos_dir / "demo-watermark", copy_project)

    def test_demo_xml(self, copy_project):
        """Test the XML demo."""
        self._run_demo_test(self._demos_dir / "demo-xml", copy_project)

    def test_overview_converter(self, copy_project):
        """Test the overview converter demo."""
        self._run_demo_test(self._demos_dir / "overview-converter", copy_project)

    def test_overview_generator(self, copy_project):
        """Test the overview generator demo."""
        self._run_demo_test(self._demos_dir / "overview-generator", copy_project)

    def test_demo_insurance(self, copy_project):
        """Test the insurance demo."""
        self._run_demo_test(self._demos_dir / "demo-insurance", copy_project)

    def test_demo_finance(self, copy_project):
        """Test the finance demo."""
        self._run_demo_test(self._demos_dir / "demo-finance", copy_project)
