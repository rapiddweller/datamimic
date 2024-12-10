# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.entities.entity_util import FieldGenerator
from datamimic_ce.generators.data_faker_generator import DataFakerGenerator
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class CreditCardEntity:
    """
    Represents a credit card entity with various attributes.

    This class provides methods to generate and access credit card-related data.
    """

    def __init__(self, class_factory_util: BaseClassFactoryUtil, locale: str | None = "en"):
        """
        Initialize the CreditCardEntity.

        Args:
            class_factory_util (BaseClassFactoryUtil): The class factory utility.
            locale (Optional[str]): The locale for generating data. Defaults to "en".
        """
        data_generation_util = class_factory_util.get_data_generation_util()
        credit_card_provider_gen = DataFakerGenerator(method="credit_card_provider", locale=locale)
        generator_fn_dict = {
            "credit_card_number": lambda: data_generation_util.generate_credit_card_number(locale),
            "card_holder": lambda: data_generation_util.generate_card_holder(locale),
            "cvc_number": lambda: data_generation_util.generate_cvc_number(),
            "expiration_date": lambda: data_generation_util.generate_expiration_date(locale),
            "credit_card_provider": lambda: credit_card_provider_gen.generate(),
        }

        self._field_generator = {}
        for key, val in generator_fn_dict.items():
            self._field_generator[key] = FieldGenerator(val)

    @property
    def credit_card_number(self):
        """
        Get the credit card number.

        Returns:
            str: The credit card number.
        """
        return self._field_generator["credit_card_number"].get()

    @property
    def card_holder(self):
        """
        Get the card holder name.

        Returns:
            str: The card holder name.
        """
        return self._field_generator["card_holder"].get()

    @property
    def cvc_number(self):
        """
        Get the CVC number.

        Returns:
            str: The CVC number.
        """
        return self._field_generator["cvc_number"].get()

    @property
    def expiration_date(self):
        """
        Get the expiration date.

        Returns:
            str: The expiration date.
        """
        return self._field_generator["expiration_date"].get()

    @property
    def credit_card_provider(self):
        """
        Get the credit card provider.

        Returns:
            str: The credit card provider.
        """
        return self._field_generator["credit_card_provider"].get()

    def reset(self):
        """
        Reset the field generators.

        This method resets all field generators to their initial state.
        """
        for key in self._field_generator:
            self._field_generator[key].reset()
