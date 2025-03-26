# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


import logging
import traceback
from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class TestDemos:
    _test_dir = Path(__file__).resolve().parent
    _project_root = Path.cwd()
    _demos_dir = _project_root / "datamimic_ce" / "demos"

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

    def _run_demo_test(self, demo_path):
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
            test_engine = DataMimicTest(test_dir=demo_path, filename="datamimic.xml")
            test_engine.test_with_timer()
            logger.info(f"Demo {demo_name} completed successfully")
        except Exception as e:
            error_msg = f"Demo {demo_name} failed with error: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            pytest.fail(error_msg)

    # Individual test methods for each demo
    def test_demo_custom_components(self):
        """Test the custom components demo."""
        self._run_demo_test(self._demos_dir / "demo-custom-components")

    def test_demo_database(self):
        """Test the database demo."""
        self._run_demo_test(self._demos_dir / "demo-database")

    def test_demo_datetime(self):
        """Test the datetime demo."""
        self._run_demo_test(self._demos_dir / "demo-datetime")

    def test_demo_db_mapping(self):
        """Test the db mapping demo."""
        self._run_demo_test(self._demos_dir / "demo-db-mapping")

    def test_demo_condition(self):
        """Test the condition demo."""
        self._run_demo_test(self._demos_dir / "demo-condition")

    def test_demo_healthcare(self):
        """Test the healthcare demo."""
        self._run_demo_test(self._demos_dir / "demo-healthcare")

    def test_demo_json(self):
        """Test the JSON demo."""
        self._run_demo_test(self._demos_dir / "demo-json")

    def test_demo_masking(self):
        """Test the masking demo."""
        self._run_demo_test(self._demos_dir / "demo-masking")

    def test_demo_model(self):
        """Test the model demo."""
        self._run_demo_test(self._demos_dir / "demo-model")

    @pytest.mark.skip(reason="Move to external service tests")
    def test_demo_mongodb(self):
        """Test the MongoDB demo."""
        self._run_demo_test(self._demos_dir / "demo-mongodb")

    def test_demo_postprocess(self):
        """Test the postprocess demo."""
        self._run_demo_test(self._demos_dir / "demo-postprocess")

    def test_demo_py_scripting(self):
        """Test the Python scripting demo."""
        self._run_demo_test(self._demos_dir / "demo-py-scripting")

    @pytest.mark.skip(reason="Move to external service tests")
    def test_demo_selector(self):
        """Test the selector demo."""
        self._run_demo_test(self._demos_dir / "demo-selector")

    def test_demo_watermark(self):
        """Test the watermark demo."""
        self._run_demo_test(self._demos_dir / "demo-watermark")

    def test_demo_xml(self):
        """Test the XML demo."""
        self._run_demo_test(self._demos_dir / "demo-xml")

    def test_overview_converter(self):
        """Test the overview converter demo."""
        self._run_demo_test(self._demos_dir / "overview-converter")

    def test_overview_generator(self):
        """Test the overview generator demo."""
        self._run_demo_test(self._demos_dir / "overview-generator")
