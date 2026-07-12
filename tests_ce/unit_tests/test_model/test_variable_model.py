# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""<variable storage=...> validation (ModelUtil.check_storage_constraints /
VariableModel.validate_storage): storage exposes a materialized source pool, so it only
combines with a plain source= (not entity=/constant=/... , not iterationSelector, not a
weighted-entity source). See datamimic_ce/tasks/variable_iterator.py for the runtime
behavior these accepted combinations enable."""

import pytest
from pydantic import ValidationError

from datamimic_ce.model.variable_model import VariableModel


class TestVariableModelStorage:
    def test_storage_invalid_value_rejected(self):
        with pytest.raises(ValidationError, match="value.*data.*iterator"):
            VariableModel(name="v", source="db1", storage="bogus")

    def test_storage_with_iteration_selector_rejected(self):
        with pytest.raises(ValidationError, match="iterationSelector"):
            VariableModel(name="v", source="db1", iterationSelector="SELECT 1", storage="data")

    def test_storage_without_source_rejected(self):
        with pytest.raises(ValidationError, match="source"):
            VariableModel(name="v", constant="fixed", storage="data")

    def test_storage_with_weighted_entity_source_rejected(self):
        with pytest.raises(ValidationError, match="weighted-entity"):
            VariableModel(name="v", source="data/x.wgt.ent.csv", storage="data")

    @pytest.mark.parametrize("storage", ["value", "data", "iterator"])
    def test_storage_with_plain_source_accepted(self, storage):
        model = VariableModel(name="v", source="db1", storage=storage)
        assert model.storage == storage
