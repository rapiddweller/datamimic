# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.entities.bank_entity import BankEntity
from datamimic_ce.entities.entity_util import EntityUtil
from datamimic_ce.generators.data_faker_generator import DataFakerGenerator
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


def checksum(iban_temp):
    """
    Calculate the checksum for an IBAN.

    Args:
        iban_temp (str): The IBAN template.

    Returns:
        int: The checksum value.
    """
    tmp = (iban_temp[4:] + iban_temp[0:4]).upper()
    digits = ""
    for c in tmp:
        if "0" <= c <= "9":
            digits += c
        elif "A" <= c <= "Z":
            n = ord(c) - ord("A") + 10
            digits += str(n // 10) + str(n % 10)
        else:
            return -1
    n = int(digits)
    return n % 97


def create_iban(dataset: str, bank_code: str, account_number: str) -> str:
    """
    Create an IBAN from the dataset, bank code, and account number.

    Args:
        dataset (str): The dataset code.
        bank_code (str): The bank code.
        account_number (str): The account number.

    Returns:
        str: The generated IBAN.
    """
    template = f"{dataset}00{bank_code}{account_number.zfill(10)}"
    remainder = checksum(template)
    pp = str(98 - remainder).zfill(2)
    return template[0:2] + pp + template[4:]


class BankAccountEntity:
    """
    Represents a bank account entity with various attributes.

    This class provides methods to generate and access bank account-related data.
    """

    def __init__(self, cls_factory_util: BaseClassFactoryUtil, locale: str, dataset: str):
        """
        Initialize the BankAccountEntity.

        Args:
            cls_factory_util (BaseClassFactoryUtil): The class factory utility.
            locale (str): The locale for generating data.
            dataset (str): The dataset code.
        """
        self._dataset = dataset
        self._bank_entity = BankEntity(cls_factory_util)
        self._account_number_generator = DataFakerGenerator(locale=locale, method="bban")

        generator_fn_dict = {
            "bank_name": lambda: self._bank_entity.name,
            "bank_code": lambda: self._bank_entity.bank_code,
            "bic": lambda: self._bank_entity.bic,
            "bin": lambda: self._bank_entity.bin,
            "account_number": lambda: self._account_number_generator.generate(),
            "iban": lambda: create_iban(self._dataset, self.bank_code, self.account_number),
        }

        self._field_generator = EntityUtil.create_field_generator_dict(generator_fn_dict)

    @property
    def bank_name(self):
        """
        Get the name of the bank.

        Returns:
            str: The name of the bank.
        """
        return self._field_generator["bank_name"].get()

    @property
    def bank_code(self):
        """
        Get the bank code.

        Returns:
            str: The bank code.
        """
        return self._field_generator["bank_code"].get()

    @property
    def bic(self):
        """
        Get the BIC (Bank Identifier Code).

        Returns:
            str: The BIC.
        """
        return self._field_generator["bic"].get()

    @property
    def bin(self):
        """
        Get the BIN (Bank Identification Number).

        Returns:
            str: The BIN.
        """
        return self._field_generator["bin"].get()

    @property
    def account_number(self):
        """
        Get the account number.

        Returns:
            str: The account number.
        """
        return self._field_generator["account_number"].get()

    @property
    def iban(self):
        """
        Get the IBAN.

        Returns:
            str: The IBAN.
        """
        return self._field_generator["iban"].get()

    def reset(self):
        """
        Reset the field generators and the bank entity.

        This method resets all field generators and the bank entity to their initial state.
        """
        for key in self._field_generator:
            self._field_generator[key].reset()
        self._bank_entity.reset()
