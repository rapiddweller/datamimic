# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


# ENV Vars are automatically retrieved from .env or
# ENVIRONMENT VARS by using extending Class BaseSettings
class Settings(BaseSettings):
    # Should be development or production
    RUNTIME_ENVIRONMENT: Literal["development", "production"] = "production"

    SC_PAGE_SIZE: int = 1000

    LIB_EDITION: str = "CE"

    RAY_DEBUG: bool = False
    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # pyright: ignore
