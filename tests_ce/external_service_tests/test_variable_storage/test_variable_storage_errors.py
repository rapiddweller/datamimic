# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""<variable storage=...> combinations that need runtime state to reject (not decidable from raw
XML attributes alone, so they can't live in VariableModel's validators - see
test_variable_model.py for the model-level combos: invalid enum, +iterationSelector, without
source, +weighted-entity). All four raise in VariableTask.__init__."""

from pathlib import Path

import pytest

from datamimic_ce.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent


def _run(filename: str) -> None:
    DataMimicTest(test_dir=_TEST_DIR, filename=filename, capture_test_result=True).test_with_timer()


def test_storage_on_lazy_script_source_rejected():
    with pytest.raises(ValueError, match="dynamic/script-evaluated source"):
        _run("fx_storage_lazy_source.xml")


def test_storage_on_global_variable_rejected():
    with pytest.raises(ValueError, match="global"):
        _run("fx_storage_global_variable.xml")


def test_storage_with_source_scripted_rejected():
    with pytest.raises(ValueError, match="sourceScripted"):
        _run("fx_storage_source_scripted.xml")


def test_storage_with_converter_rejected():
    with pytest.raises(ValueError, match="converter"):
        _run("fx_storage_converter.xml")
