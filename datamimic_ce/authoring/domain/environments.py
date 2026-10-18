# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Credential-free CE environment bindings for one Build transaction."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field

from .common import AuthoringModel, NonEmptyStrictStr


class DatabaseEnvironmentBinding(AuthoringModel):
    environment: NonEmptyStrictStr
    family: Literal["database"]


class MongoDbEnvironmentBinding(AuthoringModel):
    environment: NonEmptyStrictStr
    family: Literal["mongodb"]


ConfiguredEnvironmentBinding = Annotated[
    DatabaseEnvironmentBinding | MongoDbEnvironmentBinding, Field(discriminator="family")
]
