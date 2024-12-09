# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



import pytest
from pydantic.main import BaseModel
from pydantic.networks import AnyUrl, HttpUrl

from datamimic_ce.generators.url_generator import UrlGenerator


# TODO: Add these model into separate utils file so it can be reused
class AnyUrlModel(BaseModel):
    any_url: AnyUrl


class HttpUrlModel(BaseModel):
    http_url: HttpUrl


@pytest.mark.parametrize("_", range(5))
def test_url_generator(_):
    url = UrlGenerator().generate()
    assert url
    assert AnyUrlModel(any_url=url)


@pytest.mark.parametrize("_", range(5))
def test_url_generator_with_schemes(_):
    url = UrlGenerator(schemes=["http", "https"]).generate()
    assert url
    assert HttpUrlModel(http_url=url)
