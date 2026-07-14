# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import ATTR_SCRIPT, ATTR_TARGET, ATTR_TYPE, ATTR_URI
from datamimic_ce.constants.element_constants import EL_EXECUTE
from datamimic_ce.model.constraints import (
    EXECUTE_TYPE_VALUES,
    Constraint,
    constraints_schema_extra,
    element_constraints,
    resolved_values,
)
from datamimic_ce.model.model_util import ModelUtil

VALID_EXECUTE_TYPES: frozenset[str] = resolved_values(EXECUTE_TYPE_VALUES)


class ExecuteModel(BaseModel):
    __constraints__: ClassVar[tuple[Constraint, ...]] = element_constraints(EL_EXECUTE)
    model_config = ConfigDict(json_schema_extra=constraints_schema_extra)

    # uri (a script file) XOR inline element text; enforced by the parser, which also resolves `type`.
    uri: str | None = Field(
        None,
        description="Path to a script file to execute (.py, .sql or .sh). Mutually exclusive with "
        "inline element text and script=; when set, type= is inferred from the extension if not given.",
        examples=["script/setup.sql", "script/lib.py"],
    )
    target: str | None = Field(
        None,
        description="Client id to run the script against, required for type='sql' (e.g. a "
        "<database> id); ctx.root.clients[target].execute_sql_script(...) executes the SQL text.",
        examples=["sourceDB"],
    )
    type: str | None = Field(
        None,
        description="Execution language: 'python', 'bash' or 'sql'. Required when using script=; "
        "for uri= it is inferred from the file extension when omitted.",
        examples=["sql", "python", "bash"],
    )
    # An expression whose evaluated value IS the code to run (pairs with <variable string=.../>).
    script: str | None = Field(
        None,
        description="Expression whose evaluated string value IS the code to run (e.g. a "
        "<variable string=...> holding assembled SQL). Mutually exclusive with uri= and inline text; "
        "requires type= to be set.",
        examples=["assembled_ddl"],
    )

    @model_validator(mode="before")  # noqa: B023
    @classmethod
    def check_execute_valid_attributes(cls, values: dict[str, Any]) -> dict[str, Any]:
        return ModelUtil.check_valid_attributes(
            values=values,
            valid_attributes={ATTR_URI, ATTR_TARGET, ATTR_TYPE, ATTR_SCRIPT},
        )

    @model_validator(mode="before")
    @classmethod
    def check_execute_modes(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Enforce attribute-only execute modes; inline text remains parser-owned."""
        return ModelUtil.check_constraints(values, cls.__constraints__)

    @field_validator("type")  # noqa: B023
    @classmethod
    def validate_type(cls, value):
        if value is not None and value not in VALID_EXECUTE_TYPES:
            raise ValueError(f"'{ATTR_TYPE}' of <execute> must be one of {sorted(VALID_EXECUTE_TYPES)}, got '{value}'")
        return value
