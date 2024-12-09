# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


# ENV Vars are automatically retrieved from .env or
# ENVIRONMENT VARS by using extending Class BaseSettings
class Settings(BaseSettings):
    # Should be development or production
    RUNTIME_ENVIRONMENT: Literal["development", "production"] = "production"

    SC_PAGE_SIZE: int = 1000

    DEFAULT_LOGGER: str = "DATAMIMIC"

    LIB_EDITION: str = "CE"
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()  # pyright: ignore
