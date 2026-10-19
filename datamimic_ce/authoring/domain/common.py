# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

"""Runtime-free shared authoring transport primitives."""

from pathlib import PurePosixPath
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, ValidatorFunctionWrapHandler, WrapValidator

MAX_AUTHORING_MAX_COUNT = 1000

PositiveStrictInt = Annotated[StrictInt, Field(gt=0)]
NonNegativeStrictInt = Annotated[StrictInt, Field(ge=0)]
MAX_AUTHORING_XML_LENGTH = 1_000_000

NonEmptyStrictStr = Annotated[StrictStr, Field(min_length=1)]


def validate_workspace_descriptor_path(value: PurePosixPath) -> PurePosixPath:
    if value.is_absolute() or ".." in value.parts or value == PurePosixPath(".") or "\\" in str(value):
        raise ValueError("descriptor_path must be a non-empty relative POSIX path without '..'")
    return value


def _workspace_path(value: object, handler: ValidatorFunctionWrapHandler) -> PurePosixPath:
    # Pydantic JSON mode also validates typed defaults; they are already paths.
    path = value if isinstance(value, PurePosixPath) else handler(value)
    if not isinstance(path, PurePosixPath):
        raise ValueError("descriptor_path must be a POSIX path")
    return validate_workspace_descriptor_path(path)


WorkspaceDescriptorPath = Annotated[PurePosixPath, WrapValidator(_workspace_path)]


class AuthoringModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True, allow_inf_nan=False)


# Float-backed decimal range proof retains the previous authoring precision limit.
MAX_AUTHORING_DECIMAL_SCALE = 15
