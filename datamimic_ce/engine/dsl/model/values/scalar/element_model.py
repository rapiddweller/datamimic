# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import ClassVar

from pydantic import ConfigDict, model_validator

from datamimic_ce.engine.dsl.model.constraints import (
    ELEMENT_ARGUMENT_CONSTRAINTS,
    ELEMENT_UNSUPPORTED_CONSTRAINTS,
    Constraint,
    constraints_schema_extra,
    element_constraints,
)
from datamimic_ce.engine.dsl.model.validation import check_constraints
from datamimic_ce.engine.dsl.model.values.scalar.key_model import KeyModel
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_ELEMENT


class ElementModel(KeyModel):
    __constraints__: ClassVar[tuple[Constraint, ...]] = element_constraints(EL_ELEMENT)
    model_config = ConfigDict(json_schema_extra=constraints_schema_extra(__constraints__))

    @model_validator(mode="before")
    @classmethod
    def validate_element_refuses_attributes_it_ignores(cls, values: dict):
        return check_constraints(values, (*ELEMENT_UNSUPPORTED_CONSTRAINTS, *ELEMENT_ARGUMENT_CONSTRAINTS))
