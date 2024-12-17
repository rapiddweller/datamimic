# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com



import pytest
from pydantic import BaseModel, ValidationError
from pydantic.networks import EmailStr

from datamimic_ce.generators.email_address_generator import EmailAddressGenerator
from datamimic_ce.generators.family_name_generator import FamilyNameGenerator
from datamimic_ce.generators.given_name_generator import GivenNameGenerator


class EmailModel(BaseModel):
    email_str: EmailStr


def test_invalid_email() -> None:
    invalid_email = "hello datamimic"

    with pytest.raises(ValidationError):
        EmailModel(email_str=invalid_email)


def test_email_generator_without_name_input() -> None:
    email_address_generator = EmailAddressGenerator(dataset="US", generated_count=1)

    assert email_address_generator
    email = email_address_generator.generate()
    assert EmailModel(email_str=email)


def test_email_generator_with_name_input() -> None:
    for _ in range(10):
        given_name = GivenNameGenerator(dataset="US", generated_count=1).generate()
        assert isinstance(given_name, str)
        family_name = FamilyNameGenerator(dataset="US", generated_count=1).generate()
        assert isinstance(family_name, str)
        with_name_email_generator = EmailAddressGenerator(
            dataset="US", given_name=given_name, family_name=family_name, generated_count=1
        )

        email = with_name_email_generator.generate()

        assert EmailModel(email_str=email)
        assert given_name.lower() in email or family_name.lower() in email
