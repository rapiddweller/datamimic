# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random

from datamimic_ce.entities.entity_util import EntityUtil
from datamimic_ce.generators.data_faker_generator import DataFakerGenerator
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class BankEntity:
    """
    Represents a bank entity with various attributes.

    This class provides methods to generate and access bank-related data.
    """

    def __init__(self, class_factory_util: BaseClassFactoryUtil):
        """
        Initialize the BankEntity.

        Args:
            class_factory_util (BaseClassFactoryUtil): The class factory utility.
        """
        self._bank_code_gen = DataFakerGenerator(method="swift8")

        data_generation_util = class_factory_util.get_data_generation_util()

        generator_fn_dict = {
            "name": lambda: random.choice(["Deutsche Bank", "Dresdner Bank", "Commerzbank", "Spardabank", "HVB"]),
            "bank_code": lambda: self._bank_code_gen.generate(),
            "bic": lambda: data_generation_util.rnd_str_from_regex(r"[A-Z]{4}DE[A-Z0-9]{2}"),
            "bin": lambda: str(data_generation_util.rnd_int(0, 9999)).zfill(4),
        }
        self._field_gen = EntityUtil.create_field_generator_dict(generator_fn_dict)

    @property
    def name(self):
        """
        Get the name of the bank.

        Returns:
            str: The name of the bank.
        """
        return self._field_gen["name"].get()

    @property
    def bank_code(self):
        """
        Get the bank code.

        Returns:
            str: The bank code.
        """
        return self._field_gen["bank_code"].get()

    @property
    def bic(self):
        """
        Get the BIC (Bank Identifier Code).

        Returns:
            str: The BIC.
        """
        return self._field_gen["bic"].get()

    @property
    def bin(self):
        """
        Get the BIN (Bank Identification Number).

        Returns:
            str: The BIN.
        """
        return self._field_gen["bin"].get()

    def reset(self):
        """
        Reset the field generators.

        This method resets all field generators to their initial state.
        """
        for key in self._field_gen:
            self._field_gen[key].reset()
