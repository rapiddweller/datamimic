# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from datamimic_ce.constants.attribute_constants import ATTR_SCRIPT, ATTR_TARGET, ATTR_TYPE, ATTR_URI
from datamimic_ce.model.constraints import (
    Constraint,
    ValidValues,
    constraints_schema_extra,
)
from datamimic_ce.model.model_util import ModelUtil

# Inline/uri execution languages DATAMIMIC supports.
# Declared fact (SPOT): the literal lives ONCE here; VALID_EXECUTE_TYPES is an alias
# derived from it, and the enforcing field_validator reads the alias. Message is
# dynamic (interpolates the rejected value), so the fact carries message=None.
_EXECUTE_TYPE_VALUES = ValidValues(ATTR_TYPE, frozenset(("python", "bash", "sql")))
VALID_EXECUTE_TYPES: set[str] = set(_EXECUTE_TYPE_VALUES.values)


class ExecuteModel(BaseModel):
    # Declared cross-field constraints
    __constraints__: ClassVar[tuple[Constraint, ...]] = (
        # Same object the type field_validator reads (via the VALID_EXECUTE_TYPES alias)
        _EXECUTE_TYPE_VALUES,
    )
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

    @field_validator("type")  # noqa: B023
    @classmethod
    def validate_type(cls, value):
        if value is not None and value not in VALID_EXECUTE_TYPES:
            raise ValueError(f"'{ATTR_TYPE}' of <execute> must be one of {sorted(VALID_EXECUTE_TYPES)}, got '{value}'")
        return value
